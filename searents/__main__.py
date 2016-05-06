#!/usr/bin/env python3

"""Web Scraper for Urbana Apartments"""

import argparse
import mimetypes
import os

import fake_useragent
import requests

from survey import RentSurvey
from urbana import UrbanaScraper


def cli(parser=argparse.ArgumentParser()):
    """ Specify and get command-line parameters. """
    parser.add_argument(
        "-f", "--file",
        default="survey.json",
        help="Specify the file to read/write the survey from.",
    )
    parser.add_argument(
        "-g", "--graphical",
        help="Plot old listings (ignored without -r).",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "-r", "--read-only",
        help="Get and show old listings only.",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose",
        help="Print progress details.",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "--debug",
        help="Print parsing details (ignored with -r).",
        default=False,
        action="store_true"
    )
    return parser


def main(args):
    """Execute CLI commands."""

    survey = None
    if args.verbose:
        print('Reading {0}...'.format(args.file), end=' ')
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            survey = RentSurvey.deserialize(f.read())
        if args.verbose:
            print('{0} listings'.format(len(survey)))
    except FileNotFoundError:
        if args.read_only:
            raise
        elif args.verbose:
            print('not found')
        survey = RentSurvey()
    assert survey is not None

    if args.read_only:
        if args.graphical:
            survey.visualize()
        else:
            print(survey)
    else:

        if args.verbose:
            print('Getting new listings...')
        new_listings = RentSurvey(
            UrbanaScraper(
                verbose=args.verbose,
                debug=args.debug,
            ).scrape_listings(
                dirpath=os.path.dirname(args.file),
            )
        )

        if args.verbose:
            print('{0} new listings were found.'.format(len(new_listings)))
        print(new_listings)

        if args.verbose:
            print('Writing {0}...'.format(args.file))
        survey += new_listings
        with open(args.file, 'w', encoding='utf-8') as f:
            f.write(survey.serialize())


if __name__ == '__main__':
    main(cli().parse_args())
