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
        '--cache', '-c',
        help='Specify the directory to store scrape caches in.',
        default='searents_scrapes',
    )
    parser.add_argument(
        '--cached',
        help='Show cached listings.',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--graphical',
        help='Plot listings (requires --show).',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--no-fetch',
        help='Do not fetch new listings.',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--regenerate',
        help='Use the scrape cache to regenerate the survey (requires --verify).',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--verbose', '-v',
        help='Print progress details.',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '--verify',
        help='Verify the survey against the scrape cache.',
        default=False,
        action='store_true'
    )
    return parser


def main(args=cli().parse_args()):
    """Execute CLI commands."""

    _print = print if args.verbose else lambda *args, **kwargs: None

    scrapers = {
        'Urbana': UrbanaScraper(
            cache_path=os.path.join(args.cache, 'urbana'),
            verbose=args.verbose,
        ),
    }
    surveys = {}

    for name, scraper in scrapers.items():

        _print(name)
        survey_path = os.path.join(args.cache, '{0}.json'.format(name))
        _print('* Reading the survey at {0}...'.format(survey_path), end=' ')
        try:
            surveys[name] = RentSurvey.load(survey_path)
            _print('{0} listings'.format(len(surveys[name])))
        except FileNotFoundError:
            _print('not found')
            open(survey_path, 'a').close()
            surveys[name] = RentSurvey()

        if not args.no_fetch:
            _print('* Getting new listings...')
            survey = scraper.scrape_listings()
            before = len(surveys[name])
            surveys[name].extend(survey)
            _print('* {0} new listings were found.'.format(len(surveys[name]) - before))
            if not args.cached:
                if args.graphical:
                    survey.visualize()
                else:
                    print(survey)
            _print('* Writing the new listings to {0}...'.format(survey_path))
            surveys[name].save(survey_path)

        if args.verify:
            _print('* Generating a survey from the cache at {0}...'.format(scraper.cache_path))
            cached_survey = scraper.cached_listings()
            _print('* Verifying the generated survey with the survey at {0}...'.format(survey_path))
            if surveys[name] != cached_survey:
                _print('* The survey is not consistent with the cache.')
                if args.regenerate:
                    if args.verbose:
                        print('* Overwriting the survey at {0}...'.format(survey_path))
                    cached_survey.save(survey_path)
                    surveys[name] = cached_survey
                else:
                    return 1
            _print('* The survey is consistent with the cache.')

    if args.cached:

        _print('* Combining and sorting all surveys...')
        survey = RentSurvey(sorted(
            [listing for survey in surveys.values() for listing in survey],
            key=lambda listing: listing['timestamp'],
        ))

        if args.graphical:
            survey.visualize()
        else:
            print(survey)
        return 0


if __name__ == '__main__':
    sys.exit(main())
