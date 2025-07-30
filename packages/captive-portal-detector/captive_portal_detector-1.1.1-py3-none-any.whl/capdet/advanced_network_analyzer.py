import concurrent.futures as cf
import platform
import re
import secrets
import socket
import ssl
from concurrent.futures import as_completed
from functools import lru_cache
from ssl import TLSVersion, SSLError
from urllib.parse import urlparse

import certifi
import requests
import tldextract
from hstspreload import in_hsts_preload
from scapy.sendrecv import sniff

try:
    import dns.message
    import dns.query
    import dns.rdatatype
    import dns.flags
    import dns.resolver
except ImportError:
    dns = None

import base64
import hashlib

from capdet.network_probe import NetworkProbe
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import netifaces
from scapy.layers.l2 import getmacbyip, Ether
from scapy.all import conf as scapy_conf
from scapy.layers.inet6 import ICMPv6ND_RA, IPv6


class AdvancedNetworkAnalyzer(NetworkProbe):
    """
    Extends NetworkProbe to provide detailed analysis of network interference,
    ranking threats by severity.
    """
    INTERFERENCE_CODES = {
        -2: "Undetermined",
        -1: "No Internet",
        0: "No Interference",

        1: "Informational",
        2: "Low – Weaknesses that need hardening",
        3: "Medium – Exposure or misconfiguration",
        4: "High – Likely attack in progress",
        5: "Critical – Confirmed MITM / SSL stripping",
    }

    _insecure_form_re = re.compile(rb'<form[^>]+action\s*=\s*["\']http://', re.I)
    _hsts_header = "strict-transport-security"
    _meta_refresh_http = re.compile(
        rb'<meta[^>]+http-equiv=["\']refresh["\'][^>]+url=http:', re.I
    )
    _js_http_redirect = re.compile(
        rb'window\.location\s*=\s*["\']http://', re.I
    )
    _ARP_LOCK = "/tmp/.capdet_arp.lock"

    CONNECT_TIMEOUT = 4        # handshake
    READ_TIMEOUT    = 6        # body
    TIMEOUT_TLS     = 7        # plain seconds for socket+TLS
    TIMEOUT_MISC    = 5        # arp, ping, dnssec, etc.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is for the gateway swap check.
        self._last_gateway_mac = None
        self._hsts_cache = {}
        scapy_conf.verb = 0

    def _detect_rogue_ipv6_ra(self, timeout=5):
        """
        Sniffs for ICMPv6 Router Advertisements to detect rogue RAs.
        NOTE: Requires root/administrator privileges to run.

        Returns a list of dictionaries, each representing a detected RA.
        """
        if platform.system() == "Windows":
            # TODO: Scapy sniffing on Windows can be complex to set up (Npcap). For now, skip this.
            self.logger.warning("IPv6 RA sniffing is not reliably supported on Windows. Skipping.")
            return []

        try:
            # Sniff for ICMPv6 Router Advertisement packets for a short duration
            packets = sniff(filter="icmp6 and ip6[40] == 134", timeout=timeout, count=5)

            if not packets:
                return []

            gateways = {}
            for pkt in packets:
                if ICMPv6ND_RA in pkt:
                    source_mac = pkt[Ether].src
                    source_ip = pkt[IPv6].src

                    if source_mac not in gateways:
                        gateways[source_mac] = {"ip": source_ip, "count": 0}
                    gateways[source_mac]["count"] += 1

            # If more than one MAC is advertising itself as a router it's a high-confidence indicator of a rogue RA.
            if len(gateways) > 1:
                return gateways
        except Exception as e:
            self.logger.error(f"Error during IPv6 RA sniffing: {e}. This may be a permissions issue.")

        return []

    def _get_default_gateway_ip(self) -> str | None:
        """
        Cross-platform method to find the default gateway IP using netifaces.
        """
        try:
            gws = netifaces.gateways()
            return gws.get('default', {}).get(netifaces.AF_INET, [None])[0]
        except Exception as e:
            self.logger.error(f"Error getting gateway IP with netifaces: {e}")
            return None

    @lru_cache(maxsize=128)
    def _get_mac_for_ip(self, ip: str) -> str | None:
        """
        Cross platform function to return MAC for the given IP
        """
        if not ip:
            return None
        mac = getmacbyip(ip)
        if mac:
            # ff:ff:ff:ff:ff:ff format
            return mac.lower()
        return None


    def _e2ld(self, host: str) -> str:
        """
        Return the eTLD+1 (effective 2-level domain) for any hostname.
        tldextract uses the public-suffix list, so ‘foo.bar.co.uk’ → ‘bar.co.uk’.
        """
        ext = tldextract.extract(host)
        return f"{ext.domain}.{ext.suffix}" if ext.suffix else host

    @lru_cache(maxsize=4096)
    def _preloaded(self, domain: str) -> bool:
        """
        Cached wrapper around in_hsts_preload. 4 k cache is plenty —
        Google’s list is ~120 k names, you’ll never hit all of them in one session.
        """
        return in_hsts_preload(domain)

    def _random_host(self) -> str:
        return f"https://{secrets.token_hex(6)}.test-net.invalid/"

    def _detect_gateway_mac_swap(self):
        gw = self._get_default_gateway_ip()
        mac = self._get_mac_for_ip(gw)
        if mac is None:
            return False

        swapped = self._last_gateway_mac is not None and mac != self._last_gateway_mac
        self._last_gateway_mac = mac
        return swapped

    def _banner_probe(self):
        results = {}
        gateway_ip = self._get_default_gateway_ip()
        if not gateway_ip:
            return results

        for port, name in [(25, "smtp"), (21, "ftp")]:
            try:
                with socket.create_connection((gateway_ip, port), self.TIMEOUT_MISC) as sock:
                    banner = sock.recv(1024).decode(errors="ignore").strip()
                    results[name] = banner or "Empty Banner"
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                self.logger.debug(f"{name} closed on gateway with {e}. Skipping.")
                continue
            except Exception as e:
                self.logger.debug(f"An unexpected error occurred: {e}")
                results[name] = None
        return results


    def _dnssec_probe(self) -> str | None:
        """
        Returns
            "secure"     – resolver validates signatures
            "insecure"   – resolver ignores DNSSEC (dangerous)
            None         – cannot decide (no dnspython, timeout, etc.)
        """
        if dns is None:
            return None

        try:
            resolver_ip = dns.resolver.get_default_resolver().nameservers[0]

            def _query(name):
                q = dns.message.make_query(name, dns.rdatatype.A, want_dnssec=True)
                return dns.query.udp(q, resolver_ip, timeout=self.TIMEOUT_MISC)

            # 1. Signed, good zone should SERVE data or SERVFAIL w/ AD
            good = _query("cloudflare.com")

            # 2. Deliberately broken sigs should SERVFAIL, not give an IP
            bad = _query("dnssec-failed.org")

            # If bad query happily returns A/AAAA, resolver isn’t validating
            if any(a.rdtype == dns.rdatatype.A for a in bad.answer):
                return "insecure"

            # If bad query SERVFAILs and good one answers, resolver validates
            if good.answer and bad.rcode() == dns.rcode.SERVFAIL:
                return "secure"

        except Exception as e:
            self.logger.debug(f"DNSSEC probe error: {e}")

        return None

    def _http_probe_detailed(self, url):
        report = {
            "status": "UNKNOWN",
            "final_url": url,
            "is_ssl_stripped": False,
            "has_insecure_form": False,
            "resolved": False,
            "http_status": None,
            "hsts_missing": False,
        }

        initial = urlparse(url)
        host = initial.hostname or ""
        initial_scheme = initial.scheme
        is_https = initial_scheme == "https"

        # DNS check
        try:
            socket.getaddrinfo(host, None)
            report["resolved"] = True
        except socket.gaierror:
            report["resolved"] = False

        # Fetch
        try:
            r = requests.get(
                url,
                timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT),
                allow_redirects=True,
                headers={"User-Agent": "PinguinProbe/Advanced"},
                proxies={"http": None, "https": None},
                verify=is_https,
            )
        except requests.exceptions.SSLError:
            report["status"] = "CAPTIVE"
            return report
        except requests.exceptions.RequestException:
            if host.endswith(".invalid") and not report["resolved"]:
                report["status"] = "OK"
            elif host.lower() == "wpad":
                report["status"] = "OK"
            else:
                report["status"] = "UNKNOWN"
            return report

        # Basic fields
        report["final_url"] = r.url
        report["http_status"] = r.status_code

        # SSL-strip
        if is_https and r.url.startswith("http://"):
            report["is_ssl_stripped"] = True

        # Insecure form
        if self._insecure_form_re.search(r.content):
            report["has_insecure_form"] = True

        #  HSTS check
        final_host = urlparse(r.url).hostname or host
        base_domain = self._e2ld(final_host)
        if base_domain not in self._hsts_cache:
            self._hsts_cache[base_domain] = in_hsts_preload(base_domain)
        if self._hsts_cache[base_domain]:
            if self._hsts_header not in {h.lower() for h in r.headers}:
                report["hsts_missing"] = True

        #  Redirect analysis
        final = urlparse(r.url)
        final_scheme = final.scheme
        orig_e2ld = self._e2ld(host)
        final_e2ld = self._e2ld(final_host)

        redirect_downgrade = is_https and final_scheme == "http"
        cross_domain_redirect = final_e2ld != orig_e2ld and final_scheme in ("http", "https")
        meta_js_downgrade = (
                r.status_code == 200
                and (
                        self._meta_refresh_http.search(r.content)
                        or self._js_http_redirect.search(r.content)
                )
        )

        if report["is_ssl_stripped"] or redirect_downgrade or cross_domain_redirect or meta_js_downgrade:
            report["status"] = "CAPTIVE"
        elif (
                url in self._expected
                and self._hash(r.content) == self._expected[url]
                and r.status_code in (200, 204)
        ):
            report["status"] = "OK"
        elif host.endswith(".invalid"):
            report["status"] = "CAPTIVE" if report["resolved"] else "OK"
        elif url in self._expected:
            report["status"] = "CAPTIVE"
        elif 300 <= r.status_code < 400:
            report["status"] = "OK"
        else:
            report["status"] = "OK" if report["status"] == "UNKNOWN" else report["status"]

        return report


    def _probe_tls_wrapped(self, host):
        report = {"status": "UNKNOWN"}
        pin = self.PINNED.get(host)
        try:
            ctx = ssl.create_default_context(cafile=certifi.where())
            # We must disable hostname checking to get the cert first, then check it manually
            ctx.check_hostname = False
            with socket.create_connection((host, 443), self.TIMEOUT_TLS) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls:
                    der_cert = tls.getpeercert(binary_form=True)
                    peer_cert = tls.getpeercert()
                    cipher_name, _, key_bits = tls.cipher()
                    ocsp_resp = getattr(tls, "ocsp_response", None)
                    report.update({
                        "ocsp_missing": False,
                        "tls_version": tls.version(),
                        "cipher": cipher_name, "key_bits": key_bits,
                    })

            # Manual hostname check
            try:
                ssl.match_hostname(peer_cert, host)
                report["hostname_mismatch"] = False
            except Exception:
                report["hostname_mismatch"] = True

            # Pinning check
            cert = x509.load_der_x509_certificate(der_cert)
            spki = cert.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
            found_pin = base64.b64encode(hashlib.sha256(spki).digest()).decode()

            if found_pin == pin:
                report["status"] = "OK"
                # OCSP informational flag, only care when the pin is good
                report["ocsp_missing"] = ocsp_resp is None
            else:
                report["status"] = "CAPTIVE"

            legacy = ("RC4", "3DES", "DES", "NULL", "EXPORT")
            weak_bits = key_bits and key_bits < 112
            weak_algo = any(x in cipher_name.upper() for x in legacy)
            report["weak_cipher"] = weak_bits or weak_algo

            report["tls_version_downgrade"] = False
            try:
                ctx13 = ssl.create_default_context(cafile=certifi.where())
                ctx13.minimum_version = TLSVersion.TLSv1_3
                ctx13.maximum_version = TLSVersion.TLSv1_3
                ctx13.check_hostname  = False

                with socket.create_connection((host, 443), self.TIMEOUT_TLS) as s13:
                    with ctx13.wrap_socket(s13, server_hostname=host):
                        # If we get here the server really does support TLS-1.3
                        if report["tls_version"] != "TLSv1.3":
                            report["tls_version_downgrade"] = True
            except SSLError:
                # Either the server or the path can’t do TLS-1.3 -> no evidence of downgrade
                pass


        except Exception as e:
            self.logger.error(f"TLS probe failed for {host}: {e}")

        return report

    def _run_all_probes_detailed(self):
        # Use a known HTTPS-only site for HSTS checks
        HTTPS_PROBE = "https://www.google.com/"
        http_targets = {
            "primary": self.PRIMARY, "fallback": self.FALLBACK,
            "https_hsts_check": HTTPS_PROBE, "random_dns_hijack": self._random_host(),
            "wpad_hijack": "http://wpad/wpad.dat",
        }

        jobs = len(http_targets) + len(self.PINNED)
        workers = min(32, max(1, jobs))

        used: set[str] = set()
        results: dict[str, dict] = {}
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {}

            for tag, url in http_targets.items():
                futures[pool.submit(self._http_probe_detailed, url)] = tag
            for host in self.PINNED:
                futures[pool.submit(self._probe_tls_wrapped, host)] = f"tls:{host}"

            for fut in as_completed(futures):
                tag  = futures[fut]
                uniq = self._dedupe_tag(tag, used)
                used.add(uniq)
                results[uniq] = fut.result()

        return results

    def _dedupe_tag(self, tag: str, used: set[str]) -> str:
        if tag not in used:
            return tag
        i = 1
        while f"{tag}#{i}" in used:
            i += 1
        return f"{tag}#{i}"

    def analyze_network_interference(self):
        """
        Runs all probes and returns a comprehensive dictionary of all found issues,
        ranked by the highest severity vulnerability detected.
        """
        results = self._run_all_probes_detailed()
        tls = {k: v for k, v in results.items() if k.startswith("tls:")}
        http = {k: v for k, v in results.items() if not k.startswith("tls:")}

        found_issues = []

        # Critical
        if any(v.get("status") == "CAPTIVE" for v in tls.values()):
            failures = [k for k, v in tls.items() if v.get("status") == "CAPTIVE"]
            found_issues.append({"code": 5, "name": "Generic MITM", "details": f"TLS certificate pin mismatch on: {failures}"})
        if any(v.get("is_ssl_stripped") for v in http.values()):
            stripped = [k for k, v in http.items() if v.get("is_ssl_stripped")]
            found_issues.append({"code": 5, "name": "SSL Stripping", "details": f"SSL stripping detected on requests: {stripped}"})

        #  High
        if http.get("random_dns_hijack", {}).get("status") == "CAPTIVE":
            found_issues.append({"code": 4, "name": "DNS Hijacking", "details": "Random nonexistent domain resolved, indicating DNS hijacking."})
        if self._detect_gateway_mac_swap():
            found_issues.append({"code": 4, "name": "Rogue DHCP / Gateway Swap", "details": "Default gateway MAC address changed mid-session."})
        if any(v.get("hsts_missing") for v in http.values()):
            found_issues.append({"code": 4, "name": "HSTS Stripping", "details": "HSTS header was stripped from a preloaded domain (google.com)."})
        if any(v.get("hostname_mismatch") for v in tls.values()):
            mismatches = [k for k, v in tls.items() if v.get("hostname_mismatch")]
            found_issues.append({"code": 4, "name": "Hostname-Mismatch Cert", "details": f"TLS certificate name does not match hostname for: {mismatches}"})

        # Medium
        wpad_res = http.get("wpad_hijack", {})
        if wpad_res.get("http_status") and wpad_res.get("http_status") != 404:
            found_issues.append({"code": 3, "name": "WPAD Hijack", "details": f"WPAD file served with status {wpad_res.get('http_status')}, indicating potential proxy hijack."})
        rogue_ras = self._detect_rogue_ipv6_ra()
        if rogue_ras:
            found_issues.append({
                "code": 3,
                "name": "Potential Rogue IPv6 Router",
                "details": f"Detected multiple IPv6 router advertisements from different MACs: {rogue_ras}"
            })
        if any(v.get("has_insecure_form") for v in http.values()):
            locations = [k for k, v in http.items() if v.get("has_insecure_form")]
            found_issues.append({"code": 3, "name": "Insecure Login Form", "details": f"Insecure HTTP form detected at: {locations}"})

        # Low
        if any(v.get("tls_version_downgrade") for v in tls.values()):
            downgrades = [k for k, v in tls.items() if v.get("tls_version_downgrade")]
            found_issues.append({"code": 2, "name": "TLS-Version Downgrade", "details": f"TLS downgrade to 1.1 or older on: {downgrades}"})
        if any(v.get("weak_cipher") for v in tls.values()):
            weak_hosts = [k for k, v in tls.items() if v.get("weak_cipher")]
            found_issues.append({"code": 2, "name": "Weak Cipher Enforcement", "details": f"Weak TLS cipher suite enforced on: {weak_hosts}"})

        # Info
        dnssec_status = self._dnssec_probe()
        if dnssec_status == "insecure":
            found_issues.append({
                "code": 1,
                "name": "DNSSEC Not Validating",
                "details": "Resolver returned an A record for dnssec-failed.org — no signature checking."
            })
        if any(v.get("ocsp_missing") for k, v in tls.items() if v.get("status") == "OK"):
            missing_on = [k for k, v in tls.items() if v.get("status") == "OK" and v.get("ocsp_missing")]
            found_issues.append({"code": 1, "name": "OCSP Stapling Missing", "details": f"OCSP stapled response missing from otherwise valid TLS handshake for: {missing_on}"})
        open_banners = self._banner_probe()
        if open_banners:
            found_issues.append({"code": 1, "name": "Open SMTP/FTP Banner", "details": f"Gateway has open, non-essential ports: {open_banners}"})

        if found_issues:
            top = max(found_issues, key=lambda x: x["code"])
            return {
                "overall_code": top["code"],
                "description": self.INTERFERENCE_CODES[top["code"]],
                "issues": sorted(found_issues, key=lambda x: x["code"], reverse=True),
                "raw_details": results,
            }

        http_ok  = any(http[k].get("status") == "OK" for k in ("primary", "fallback") if k in http)
        tls_ok   = any(v.get("status") == "OK" for v in tls.values())

        if http_ok or tls_ok:
            # Internet reachable, no security findings
            return {
                "overall_code": 0,
                "description": "No Interference",
                "issues": [],
                "raw_details": results,
            }

        # If neither HTTP nor TLS worked but DNS resolved, probably captive
        if any(v.get("resolved") for v in http.values()):
            return {
                "overall_code": 3,
                "description": "Benign Captive Portal",
                "issues": [],
                "raw_details": results,
            }

        return {
            "overall_code": -1,
            "description": "No Internet",
            "issues": [],
            "raw_details": results,
        }
