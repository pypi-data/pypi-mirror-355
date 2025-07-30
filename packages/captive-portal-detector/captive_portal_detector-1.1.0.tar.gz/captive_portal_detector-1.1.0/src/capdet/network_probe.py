import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

import concurrent.futures as cf
import hashlib
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
import random
import re
import socket
import time
import ssl
import base64

import certifi
import requests
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


class NetworkProbe:
    """
    Probes network connectivity and captive portal detection.
    Uses multiple methods to determine if the network is reachable or if a captive portal is present.
    """
    def __init__(self, _last_run=0, _last_res="NO_INTERNET", pinned_hosts=None):
        self.logger = logging.getLogger(__name__)

        self._last_run = _last_run
        self._last_res = _last_res

        if pinned_hosts is None:
            self.PINNED = {
                "c1.probecheck.fyi": "lqyY07fPMm04VfvIaguNnEQ9knCyw/KDUF8j7NPqFKE=",
                "c2.probecheck.fyi": "ugJl+63TCZaBN590TLK1mRJEseOqqYQ72aF5iYC1FFU=",
            }
        else:
            self.PINNED = pinned_hosts

    PRIMARY = "http://clients3.google.com/generate_204"
    FALLBACK = "http://detectportal.firefox.com/success.txt"

    IPV6_PLAIN = "http://[2606:4700:4700::1111]/"
    TIMEOUT = 5
    CACHE_TTL = 30

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    _expected = {
        PRIMARY:  hashlib.sha256(b"").hexdigest(),
        FALLBACK: hashlib.sha256(b"success\n").hexdigest(),
    }

    _meta  = re.compile(rb"<meta[^>]http-equiv=['\"]?refresh", re.I)
    _jsloc = re.compile(rb"location\.(href|replace)", re.I)

    def _hash(self, b):    return hashlib.sha256(b).hexdigest()

    def _tls_probe(self, host: str) -> str:
        """
        Perform TLS handshake, hash the peer cert, compare to PINNED[host].
        OK if match, CAPTIVE if mismatch, UNKNOWN on network errors.
        """
        pin = self.PINNED.get(host)
        if not pin:
            return "UNKNOWN"

        try:
            ctx = ssl.create_default_context(cafile=certifi.where())
            with socket.create_connection((host, 443), self.TIMEOUT) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls:
                    der = tls.getpeercert(binary_form=True)
        except (socket.timeout, socket.gaierror, ssl.SSLError, ConnectionRefusedError, OSError) as e:
            self.logger.error(f"Error during _tls_probe: {e}")
            return "UNKNOWN"

        cert = x509.load_der_x509_certificate(der)
        pubkey = cert.public_key()
        spki_bytes = pubkey.public_bytes(
            encoding=Encoding.DER,
            format=PublicFormat.SubjectPublicKeyInfo
        )
        h = hashlib.sha256(spki_bytes).digest()
        found = base64.b64encode(h).decode()

        return "OK" if found == pin else "CAPTIVE"

    def _random_host(self):
        if not self.PINNED:
            return f"https://{random.randint(0,2**32):x}.probecheck.fyi/"

        random_host_key = random.choice(list(self.PINNED.keys()))
        parent_domain = ".".join(random_host_key.split('.')[1:])
        return f"https://{random.randint(0,2**32):x}.{parent_domain}/"

    def _single(self, url):
        # NOTE: verify=False is intentional to see captive-portal tampering,
        # so TLS failures must not abort the probe.
        try:
            r = requests.get(url, timeout=self.TIMEOUT, allow_redirects=False,
                             headers={"User-Agent":self.USER_AGENT},
                             proxies={"http":None,"https":None}, verify=False)
        except requests.exceptions.Timeout:
            self.logger.warning(f"_single receiving timeout error, retrying...")
            try:
                r = requests.get(url, timeout=self.TIMEOUT*2, allow_redirects=False,
                                 headers={"User-Agent":self.USER_AGENT},
                                 proxies={"http":None,"https":None}, verify=False)
            except requests.exceptions.Timeout:
                self.logger.error(f"Timeout error on second attempt, returning CAPTIVE")
                return "CAPTIVE"
        except requests.exceptions.ConnectionError:
            # expected path for the random probe on a healthy network
            return "UNKNOWN"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Unhandled request exception for {url}: {e}")
            return "UNKNOWN"

        # A redirect is always a captive portal
        if r.status_code in (301, 302, 303, 307, 308):
            return "CAPTIVE"

        # HTMLand js based redirects are also captive portals
        if r.status_code == 200 and (self._meta.search(r.content) or self._jsloc.search(r.content)):
            return "CAPTIVE"

        if url in self._expected and self._hash(r.content) == self._expected[url] and r.status_code in (200, 204):
            return "OK"

        # If the probe was NOT a standard one and we received a 200 OK, the request to a non-existent domain
        # was successfully intercepted
        if url not in self._expected and r.status_code == 200:
            self.logger.warning(f"Received 200 OK from unexpected URL {url}, indicating captive portal.")
            return "CAPTIVE"

        return "UNKNOWN"

    def _run_probes(self):
        """Runs all probes and returns a dictionary of their raw results."""
        http_probes = {
            "primary":  self.PRIMARY,
            "fallback": self.FALLBACK,
            "ipv6":     self.IPV6_PLAIN,
            "random":   self._random_host(),
        }

        all_probes = http_probes | self.PINNED

        with cf.ThreadPoolExecutor(max_workers=len(all_probes)) as pool:
            # launch all HTTP probes
            futs = {pool.submit(self._single, url): tag for tag, url in http_probes.items()}
            # launch one TLS probe per pinned host
            for host in self.PINNED:
                futs[pool.submit(self._tls_probe, host)] = f"tls:{host}"

        results = {k: f.result() for f, k in futs.items()}
        self.logger.info(f"Probe results: {results}")
        return results

    def network_health(self, force=False):
        """
        Provides a simple verdict on network health: OK, CAPTIVE, or NO_INTERNET.
        """
        if not force and time.time() - self._last_run < self.CACHE_TTL:
            return self._last_res

        res = self._run_probes()
        pinned_results = {res[k] for k in res if k.startswith("tls:")}

        if "CAPTIVE" in res.values(): # A pin mismatch is always definitive
            verdict = "CAPTIVE"
        elif "OK" in pinned_results:  # Trust an OK only if it comes from a pinned probe
            verdict = "OK"
        else: # No pinned OK, and no pin mismatch. Either servers are down or no internet.
            verdict = "NO_INTERNET"

        self._last_run = time.time()
        self._last_res = verdict
        return verdict
