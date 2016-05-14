#!/usr/bin/env python3

"""Web Scraper for Urbana Apartments"""

import argparse
import os
import sys

from .survey import RentSurvey
from .urbana import UrbanaScraper


def cli(parser=argparse.ArgumentParser()):
    """ Specify and get command-line parameters. """
    parser.add_argument(
        "-c", "--cache",
        help="Specify the directory to cache scrapes in.",
        default="scrapes",
    )
    parser.add_argument(
        "-f", "--file",
        help="Specify the file to read/write the survey from.",
        default="survey.json",
    )
    parser.add_argument(
        "-g", "--graphical",
        help="Plot old listings (requires -r).",
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
        "--regenerate",
        help="Use the scrape cache to regenerate the survey (requires --verify).",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "--verify",
        help="Verify the survey against the scrape cache.",
        default=False,
        action="store_true"
    )
    return parser


def main(args=cli().parse_args()):  # pylint: disable=too-many-statements, too-many-branches
    """Execute CLI commands."""

    survey = None
    if args.verbose:
        print('Reading {0}...'.format(args.file), end=' ')
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            survey = RentSurvey(sorted(
                RentSurvey.deserialize(f.read()),
                key=lambda listing: listing['timestamp'],
            ))
        if args.verbose:
            print('{0} listings'.format(len(survey)))
    except FileNotFoundError:
        if args.verbose:
            print('not found')
        survey = RentSurvey()
    assert survey is not None

    if args.read_only:
        if args.graphical:
            survey.visualize()
        else:
            print(survey)
        return 0

    urbana = UrbanaScraper(cache_path=os.path.join(args.cache, 'urbana'), verbose=args.verbose)

    if args.verify:
        if args.verbose:
            print('Verifying the Urbana survey...')
        survey.verify()
        if args.verbose:
            print('Generating the Urbana cache survey...')
        cached_listings = RentSurvey(
            sorted(urbana.cached_listings(), key=lambda listing: listing['timestamp'])
        )
        if args.verbose:
            print('Verifying the Urbana cache survey...')
        cached_listings.verify()
        if survey != cached_listings:
            if args.verbose:
                print('The survey is not consistent with the scrape cache.')
                if len(cached_listings) != len(survey):
                    print(
                        'The survey is {0}.'.format(
                            'shorter' if len(survey) < len(cached_listings) else 'longer',
                        ),
                    )
            if args.regenerate:
                if args.verbose:
                    print('Overwriting the survey...')
                with open(args.file, 'w') as f:
                    f.write(cached_listings.serialize())
                survey = cached_listings
            else:
                return 1
        if args.verbose:
            print('The survey is consistent with the scrape cache.')
        return 0

    if args.verbose:
        print('Getting new listings...')
    new_listings = urbana.scrape_listings()
    if args.verbose:
        print('{0} new listings were found.'.format(len(new_listings)))
    print(new_listings)
    survey += new_listings

    if args.verbose:
        print('Writing {0}...'.format(args.file))
    with open(args.file, 'w', encoding='utf-8') as f:
        f.write(survey.serialize())


if __name__ == '__main__':
    sys.exit(main())
