import argparse
import json
import logging
import sys

from capdet.detector import NetworkProbe
from capdet.advanced_network_analyzer import AdvancedNetworkAnalyzer

try:
    from rich import print as rprint
    from rich.table import Table
except ImportError:
    rprint = print

def _pretty(report):
    lvl = report["overall_code"]
    rprint(f"[bold]Severity {lvl} – {report['description']}[/bold]")
    if report["issues"]:
        t = Table(show_header=True, header_style="bold magenta")
        t.add_column("Code", justify="right")
        t.add_column("Issue")
        t.add_column("Details", overflow="fold")
        for i in report["issues"]:
            t.add_row(str(i["code"]), i["name"], i["details"])
        rprint(t)
    else:
        rprint("[green]No security interference detected[/green]")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    p = argparse.ArgumentParser(prog="capdet")
    p.add_argument("-a", "--advanced", action="store_true", help="run Advanced analyzer")
    p.add_argument("--json", action="store_true", help="dump raw JSON")
    args = p.parse_args()

    result = (AdvancedNetworkAnalyzer().analyze_network_interference()
              if args.advanced else NetworkProbe().network_health())

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print("\n")
    if args.advanced:
        _pretty(result)
    else:
        print(result)
