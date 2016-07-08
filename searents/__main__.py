"""Web Scraper for Seattle Apartments"""

import argparse
import logging
import os
import re
import sys

from searents.survey import RentSurvey
from searents.equity import EquityScraper


def fetch_handler(args, scrapers):  # pylint: disable=unused-argument
    """Fetch new listings."""

    for name, scraper in scrapers.items():

        survey = RentSurvey(path='{0}.json'.format(scraper.cache_path))
        survey.load()

        logging.debug('Fetching new listings from %s...', name)
        before = len(survey.listings)
        survey.listings.extend(scraper.scrape_listings().listings)
        logging.info('%d new listings were fetched.', len(survey.listings) - before)

        print(survey)

        logging.info('Writing the new listings to %s...', survey.path)
        survey.save()


def show_handler(args, scrapers):
    """Show listings."""

    for name, scraper in scrapers.items():

        survey = RentSurvey(path='{0}.json'.format(scraper.cache_path))
        survey.load()

        logging.debug('Sorting the %s survey...', name)
        survey.listings.sort(key=lambda listing: listing['timestamp'])

        logging.debug('Filtering listings...')
        filtered_listings = []
        for listing in survey.listings:
            for k, value in listing.items():
                if re.search(args.filter_key, str(k)) is not None and \
                        re.search(args.filter, str(value)) is not None:
                    filtered_listings.append(listing)
                    break
        survey.listings = filtered_listings

        if len(survey.listings) > 0:
            logging.debug('Showing the %s survey...', name)
            if args.graphical:
                survey.visualize(name)
            else:
                print(survey)


def verify_handler(args, scrapers):
    """Verify the survey against the scrape cache."""

    for name, scraper in scrapers.items():

        survey = RentSurvey(path='{0}.json'.format(scraper.cache_path))
        survey.load()

        logging.debug('Generating a survey from the cache at %s...', scraper.cache_path)
        cached_survey = scraper.cached_listings()

        if args.regenerate:
            logging.info('Overwriting the survey at %s...', survey.path)
            survey.listings = cached_survey.listings
            survey.save()

        logging.info('Verifying the %s survey...', name)
        if survey != cached_survey:
            return 1


def cli(parser=None):
    """Parse CLI arguments and options."""

    if parser is None:
        parser = argparse.ArgumentParser()

    parser.add_argument(
        '--cache', '-c',
        help='Specify the directory to store scrape caches in.',
        default='searents_scrapes',
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
        '--scraper',
        help='Specify a search pattern for scraper names.',
        default=".*",
    )

    subparsers = parser.add_subparsers()

    fetch_parser = subparsers.add_parser(
        'fetch',
        help=fetch_handler.__doc__,
    )
    fetch_parser.set_defaults(func=fetch_handler)

    show_parser = subparsers.add_parser(
        'show',
        help=show_handler.__doc__,
    )
    show_parser.add_argument(
        '--filter', '-f',
        help='Specify a regex to filter listings.',
        default='.*',
    )
    show_parser.add_argument(
        '--filter-key', '-k',
        help='Specify a regex to filter listings by key.',
        default='.*',
    )
    show_parser.add_argument(
        '--graphical',
        help='Plot listings.',
        default=False,
        action='store_true',
    )
    show_parser.set_defaults(func=show_handler)

    verify_parser = subparsers.add_parser(
        'verify',
        help=verify_handler.__doc__,
    )
    verify_parser.add_argument(
        '--regenerate',
        help='Use the scrape cache to regenerate the survey.',
        default=False,
        action='store_true',
    )
    verify_parser.set_defaults(func=verify_handler)

    return parser


def main(args=None):
    """Execute CLI commands."""

    if args is None:
        args = cli().parse_args()

    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)
    logging.basicConfig(
        filename=args.log_file,
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # pylint: disable=line-too-long
    scrapers = {
        '2300 Elliott': EquityScraper(
            url='http://www.equityapartments.com/seattle/belltown/2300-elliott-apartments',
            cache_path=os.path.join(args.cache, '2300_Elliott'),
        ),
        'Alcyone': EquityScraper(
            url='http://www.equityapartments.com/seattle/south-lake-union/alcyone-apartments',
            cache_path=os.path.join(args.cache, 'Alcyone'),
        ),
        'Bellevue Meadows': EquityScraper(
            url='http://www.equityapartments.com/seattle/redmond/bellevue-meadows-apartments',
            cache_path=os.path.join(args.cache, 'Bellevue_Meadows'),
        ),
        'Centennial Tower and Court': EquityScraper(
            url='http://www.equityapartments.com/seattle/belltown/centennial-tower-and-court-apartments',
            cache_path=os.path.join(args.cache, 'Centennial_Tower_and_Court'),
        ),
        'Chelsea Square': EquityScraper(
            url='http://www.equityapartments.com/seattle/downtown-redmond/chelsea-square-apartments',
            cache_path=os.path.join(args.cache, 'Chelsea_Square'),
        ),
        'City Square Bellevue': EquityScraper(
            url='http://www.equityapartments.com/seattle/downtown-bellevue/city-square-bellevue-apartments',
            cache_path=os.path.join(args.cache, 'City_Square_Bellevue'),
        ),
        'Harbor Steps': EquityScraper(
            url='http://www.equityapartments.com/seattle/downtown-seattle/harbor-steps-apartments',
            cache_path=os.path.join(args.cache, 'Harbor_Steps'),
        ),
        'Heritage Ridge': EquityScraper(
            url='http://www.equityapartments.com/seattle/lynnwood/heritage-ridge-apartments',
            cache_path=os.path.join(args.cache, 'Heritage_Ridge'),
        ),
        'Harrison Square': EquityScraper(
            url='http://www.equityapartments.com/seattle/lower-queen-anne/harrison-square-apartments',
            cache_path=os.path.join(args.cache, 'Harrison_Square'),
        ),
        'Ivorywood': EquityScraper(
            url='http://www.equityapartments.com/seattle/bothell/ivorywood-apartments',
            cache_path=os.path.join(args.cache, 'Ivorywood'),
        ),
        'Junction 47': EquityScraper(
            url='http://www.equityapartments.com/seattle/west-seattle/junction-47-apartments',
            cache_path=os.path.join(args.cache, 'Junction_47'),
        ),
        'Metro on First': EquityScraper(
            url='http://www.equityapartments.com/seattle/lower-queen-anne/metro-on-first-apartments',
            cache_path=os.path.join(args.cache, 'Metro_on_First'),
        ),
        'Moda': EquityScraper(
            url='http://www.equityapartments.com/seattle/belltown/moda-apartments',
            cache_path=os.path.join(args.cache, 'Moda'),
        ),
        'Monterra in Mill Creek': EquityScraper(
            url='http://www.equityapartments.com/seattle/mill-creek/monterra-in-mill-creek-apartments',
            cache_path=os.path.join(args.cache, 'Monterra_in_Mill_Creek'),
        ),
        'Odin': EquityScraper(
            url='http://www.equityapartments.com/seattle/ballard/odin-apartments',
            cache_path=os.path.join(args.cache, 'Odin'),
        ),
        'Old Town Lofts': EquityScraper(
            url='http://www.equityapartments.com/seattle/downtown-redmond/old-town-lofts-apartments',
            cache_path=os.path.join(args.cache, 'Old_Town_Lofts'),
        ),
        'Olympus': EquityScraper(
            url='http://www.equityapartments.com/seattle/belltown/olympus-apartments',
            cache_path=os.path.join(args.cache, 'Olympus'),
        ),
        'Packard Building': EquityScraper(
            url='http://www.equityapartments.com/seattle/capitiol-hill/packard-building-apartments',
            cache_path=os.path.join(args.cache, 'Packard_Building'),
        ),
        'Providence': EquityScraper(
            url='http://www.equityapartments.com/seattle/bothell/providence-apartments',
            cache_path=os.path.join(args.cache, 'Providence'),
        ),
        'Red160': EquityScraper(
            url='http://www.equityapartments.com/seattle/downtown-redmond/red160-apartments',
            cache_path=os.path.join(args.cache, 'Red160'),
        ),
        'Redmond Court': EquityScraper(
            url='http://www.equityapartments.com/seattle/redmond/redmond-court-apartments',
            cache_path=os.path.join(args.cache, 'Redmond_Court'),
        ),
        'Rianna': EquityScraper(
            url='http://www.equityapartments.com/seattle/capitol-hill/rianna-apartments',
            cache_path=os.path.join(args.cache, 'Rianna'),
        ),
        'Riverpark': EquityScraper(
            url='http://www.equityapartments.com/seattle/downtown-redmond/riverpark-apartments',
            cache_path=os.path.join(args.cache, 'Riverpark'),
        ),
        'Seventh and James': EquityScraper(
            url='http://www.equityapartments.com/seattle/first-hill/seventh-and-james-apartments',
            cache_path=os.path.join(args.cache, 'Seventh_and_James'),
        ),
        'Square One': EquityScraper(
            url='http://www.equityapartments.com/seattle/roosevelt/square-one-apartments',
            cache_path=os.path.join(args.cache, 'Square_One'),
        ),
        'Surrey Downs': EquityScraper(
            url='http://www.equityapartments.com/seattle/factoria/surrey-downs-apartments',
            cache_path=os.path.join(args.cache, 'Surrey_Downs'),
        ),
        'The Heights on Capitol Hill': EquityScraper(
            url='http://www.equityapartments.com/seattle/capitol-hill/the-heights-on-capitol-hill-apartments',
            cache_path=os.path.join(args.cache, 'The_Heights_on_Capitol_Hill'),
        ),
        'The Pearl': EquityScraper(
            url='http://www.equityapartments.com/seattle/capitiol-hill/the-pearl-apartments-capitol-hill',
            cache_path=os.path.join(args.cache, 'The_Pearl'),
        ),
        'The Reserve at Town Center': EquityScraper(
            url='http://www.equityapartments.com/seattle/mill-creek/the-reserve-at-town-center-apartments',
            cache_path=os.path.join(args.cache, 'The_Reserve_at_Town_Center'),
        ),
        'Three20': EquityScraper(
            url='http://www.equityapartments.com/seattle/capitol-hill/three20-apartments',
            cache_path=os.path.join(args.cache, 'Three20'),
        ),
        'Urbana': EquityScraper(
            url='http://www.equityapartments.com/seattle/ballard/urbana-apartments',
            cache_path=os.path.join(args.cache, 'Urbana'),
        ),
        'Uwajimaya Village': EquityScraper(
            url='http://www.equityapartments.com/seattle/international-district/uwajimaya-village-apartments',
            cache_path=os.path.join(args.cache, 'Uwajimaya_Village'),
        ),
        'Veloce': EquityScraper(
            url='http://www.equityapartments.com/seattle/downtown-redmond/veloce-apartments',
            cache_path=os.path.join(args.cache, 'Veloce'),
        ),
    }
    # pylint: enable=line-too-long

    return args.func(
        args,
        {
            name: scraper
            for name, scraper in scrapers.items()
            if re.search(args.scraper, name) is not None
        },
    )


if __name__ == '__main__':
    sys.exit(main())
