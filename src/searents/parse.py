"""Show raw parse data."""

import argparse
import json

from searents.equity import EquityParser


def cli(parser=None):
    """Parse CLI commands."""
    if parser is None:
        parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        help="Specify the directory to store scrape caches in.",
    )
    return parser


def main(args=None):
    """Execute CLI commands."""
    if args is None:
        args = cli().parse_args()
    with open(args.path, "r", encoding="utf-8") as scrape_f:
        html = scrape_f.read()
    parser = EquityParser()
    parser.feed(html)
    print(json.dumps(parser.units, indent=4))
    return 0
