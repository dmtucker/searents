#!/usr/bin/env python3

"""Web Scraper for Urbana Apartments"""

import argparse
import logging
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
        action='store_true',
    )
    parser.add_argument(
        '--graphical',
        help='Plot listings (requires --show).',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--no-fetch',
        help='Do not fetch new listings.',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--regenerate',
        help='Use the scrape cache to regenerate the survey (requires --verify).',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--log-file',
        help='Specify the directory to store scrape caches in.',
        default=os.path.join('/var', 'log', 'searents.log'),
    )
    parser.add_argument(
        '--log-level',
        help='Specify a log-level (DEBUG, INFO, WARNING, ERROR, CRITICAL).',
        default='INFO',
    )
    parser.add_argument(
        '--verify',
        help='Verify the survey against the scrape cache.',
        default=False,
        action='store_true',
    )
    return parser


def main(args=cli().parse_args()):  # pylint: disable=too-many-branches
    """Execute CLI commands."""

    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)
    logging.basicConfig(
        filename=args.log_file,
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    scrapers = {
        'Urbana': UrbanaScraper(cache_path=os.path.join(args.cache, 'Urbana')),
    }
    surveys = {}

    for name, scraper in scrapers.items():

        if not args.graphical:
            print(name)
        survey_path = os.path.join(args.cache, '{0}.json'.format(name))
        logging.info('Reading the survey at %s...', survey_path)
        try:
            surveys[name] = RentSurvey.load(survey_path)
            logging.debug('%d listings', len(surveys[name]))
        except FileNotFoundError:
            logging.debug('%s not found', survey_path)
            open(survey_path, 'a').close()
            surveys[name] = RentSurvey()

        if not args.no_fetch:
            logging.debug('Fetching new listings...')
            survey = scraper.scrape_listings()
            before = len(surveys[name])
            surveys[name].extend(survey)
            logging.info('%d new listings were fetched.', len(surveys[name]) - before)
            if not args.cached:
                if args.graphical:
                    survey.visualize(name)
                else:
                    print(survey)
            logging.info('Writing the new listings to %s...', survey_path)
            surveys[name].save(survey_path)

        if args.verify:
            logging.debug('Generating a survey from the cache at %s...', scraper.cache_path)
            cached_survey = scraper.cached_listings()
            logging.info('Verifying the generated survey with the survey at %s...', survey_path)
            if surveys[name] != cached_survey:
                logging.info('The survey is not consistent with the cache.')
                if args.regenerate:
                    logging.info('Overwriting the survey at %s...', survey_path)
                    cached_survey.save(survey_path)
                    surveys[name] = cached_survey
                else:
                    return 1
            logging.info('The survey is consistent with the cache.')

    if args.cached:

        logging.debug('Combining and sorting all surveys...')
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
