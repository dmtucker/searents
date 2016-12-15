"""Web Scraper for Seattle Apartments"""

import argparse
import logging
import os
import re
import sqlite3
import sys
import time

import dateutil.parser

from searents.survey import RentSurvey
from searents.equity import EquityScraper


def database_connection(*args, **kwargs):
    """Create a connection to the database."""
    kwargs['detect_types'] = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    sqlite3.register_converter('TIMESTAMP', dateutil.parser.parse)
    connection = sqlite3.connect(*args, **kwargs)
    connection.row_factory = sqlite3.Row
    connection.execute(
        'CREATE TABLE IF NOT EXISTS listings'
        '(timestamp TIMESTAMP, url TEXT, scraper TEXT, unit TEXT, price REAL)'
    )
    connection.commit()
    return connection


def fetch_handler(args, scrapers, connection):
    """Fetch new listings."""

    for scraper in scrapers:

        logging.info('Fetching new listings from %s...', scraper.name)
        survey = scraper.scrape_survey()

        logging.info('%d new listings were fetched.', len(survey.listings))
        print(survey)

        logging.info('Writing the new listings to the database at %s...', args.database)
        connection.executemany(
            'INSERT INTO listings VALUES (?, ?, ?, ?, ?)',
            [
                (
                    listing['timestamp'],
                    listing['url'],
                    scraper.name,
                    listing['unit'],
                    listing['price'],
                )
                for listing in survey.listings
            ],
        )
        connection.commit()


def regenerate_handler(args, scrapers, connection):
    """Create a database from the scrape cache."""

    logging.info('Recreating the database at %s...', args.database)
    connection.close()
    if os.path.exists(args.database):
        os.rename(args.database, args.database + '.' + str(time.time()))
    connection = database_connection(args.database)

    for scraper in scrapers:

        logging.info('Generating a survey from the cache at %s...', scraper.cache_path)
        survey = scraper.cache_survey

        logging.info('Writing the %s survey to the database...', scraper.name)
        connection.executemany(
            'INSERT INTO listings VALUES (?, ?, ?, ?, ?)',
            [
                (
                    listing['timestamp'],
                    listing['url'],
                    scraper.name,
                    listing['unit'],
                    listing['price'],
                )
                for listing in survey.listings
            ],
        )
        connection.commit()

    connection.close()
    sys.exit()


def show_handler(args, scrapers, connection):
    """Show listings."""

    for scraper in scrapers:

        logging.info('Reading %s listings from the database at %s...', scraper.name, args.database)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM listings WHERE scraper=?', (scraper.name,))
        survey = RentSurvey(listings=[dict(row) for row in cursor.fetchall()])

        logging.info('Filtering %s listings...', scraper.name)
        survey.listings = [
            listing
            for listing in sorted(survey.listings, key=lambda _listing: _listing['timestamp'])
            if any(
                re.search(args.filter_key, str(key)) is not None and
                re.search(args.filter, str(value)) is not None
                for key, value in listing.items()
            )
        ]

        if len(survey.listings) > 0:
            logging.info('Showing the %s survey...', scraper.name)
            if args.graphical:
                survey.visualize(scraper.name)
            else:
                print(survey)


def verify_handler(args, scrapers, connection):
    """Verify the database against the scrape cache."""

    for scraper in scrapers:

        logging.info('Reading %s listings from the database at %s...', scraper.name, args.database)
        cursor = connection.execute('SELECT * FROM listings WHERE scraper=?', (scraper.name,))
        survey = RentSurvey(listings=[dict(row) for row in cursor.fetchall()])

        logging.info('Generating a survey from the cache at %s...', scraper.cache_path)
        cache_survey = scraper.cache_survey

        logging.info('Verifying the %s survey...', scraper.name)
        if survey != cache_survey:
            return 1


def cli(parser=None):
    """Parse CLI arguments and options."""

    if parser is None:
        parser = argparse.ArgumentParser()

    parser.add_argument(
        '--cache', '-c',
        help='Specify the directory to store scrape caches in.',
        default=os.path.join('{directory}', 'cache'),
    )
    parser.add_argument(
        '--directory',
        help='Specify a directory to store a cache, database, and log in.',
        default=os.path.join(os.environ.get('HOME', ''), '.searents'),
    )
    parser.add_argument(
        '--database',
        help='Specify a SeaRents database.',
        default=os.path.join('{directory}', 'searents.db'),
    )
    parser.add_argument(
        '--log-file',
        help='Specify the file to log to.',
        default=os.path.join('{directory}', 'searents.log'),
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

    regenerate_parser = subparsers.add_parser(
        'regenerate',
        help=regenerate_handler.__doc__,
    )
    regenerate_parser.set_defaults(func=regenerate_handler)

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
        '--graphical', '-g',
        help='Plot listings.',
        default=False,
        action='store_true',
    )
    show_parser.set_defaults(func=show_handler)

    verify_parser = subparsers.add_parser(
        'verify',
        help=verify_handler.__doc__,
    )
    verify_parser.set_defaults(func=verify_handler)

    return parser


def main(args=None):
    """Execute CLI commands."""

    if args is None:
        args = cli().parse_args()

    os.makedirs(args.directory, exist_ok=True)
    args.cache = args.cache.format(directory=args.directory)
    args.database = args.database.format(directory=args.directory)
    args.log_file = args.log_file.format(directory=args.directory)

    connection = database_connection(args.database)

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
    scrapers = [
        EquityScraper(
            name='2300 Elliott',
            url='http://www.equityapartments.com/seattle/belltown/2300-elliott-apartments',
            cache_path=os.path.join(args.cache, '2300_Elliott'),
        ),
        EquityScraper(
            name='Alcyone',
            url='http://www.equityapartments.com/seattle/south-lake-union/alcyone-apartments',
            cache_path=os.path.join(args.cache, 'Alcyone'),
        ),
        EquityScraper(
            name='Bellevue Meadows',
            url='http://www.equityapartments.com/seattle/redmond/bellevue-meadows-apartments',
            cache_path=os.path.join(args.cache, 'Bellevue_Meadows'),
        ),
        EquityScraper(
            name='Centennial Tower and Court',
            url='http://www.equityapartments.com/seattle/belltown/centennial-tower-and-court-apartments',
            cache_path=os.path.join(args.cache, 'Centennial_Tower_and_Court'),
        ),
        EquityScraper(
            name='Chelsea Square',
            url='http://www.equityapartments.com/seattle/downtown-redmond/chelsea-square-apartments',
            cache_path=os.path.join(args.cache, 'Chelsea_Square'),
        ),
        EquityScraper(
            name='City Square Bellevue',
            url='http://www.equityapartments.com/seattle/downtown-bellevue/city-square-bellevue-apartments',
            cache_path=os.path.join(args.cache, 'City_Square_Bellevue'),
        ),
        EquityScraper(
            name='Harbor Steps',
            url='http://www.equityapartments.com/seattle/downtown-seattle/harbor-steps-apartments',
            cache_path=os.path.join(args.cache, 'Harbor_Steps'),
        ),
        EquityScraper(
            name='Heritage Ridge',
            url='http://www.equityapartments.com/seattle/lynnwood/heritage-ridge-apartments',
            cache_path=os.path.join(args.cache, 'Heritage_Ridge'),
        ),
        EquityScraper(
            name='Harrison Square',
            url='http://www.equityapartments.com/seattle/lower-queen-anne/harrison-square-apartments',
            cache_path=os.path.join(args.cache, 'Harrison_Square'),
        ),
        EquityScraper(
            name='Ivorywood',
            url='http://www.equityapartments.com/seattle/bothell/ivorywood-apartments',
            cache_path=os.path.join(args.cache, 'Ivorywood'),
        ),
        EquityScraper(
            name='Junction 47',
            url='http://www.equityapartments.com/seattle/west-seattle/junction-47-apartments',
            cache_path=os.path.join(args.cache, 'Junction_47'),
        ),
        EquityScraper(
            name='Metro on First',
            url='http://www.equityapartments.com/seattle/lower-queen-anne/metro-on-first-apartments',
            cache_path=os.path.join(args.cache, 'Metro_on_First'),
        ),
        EquityScraper(
            name='Moda',
            url='http://www.equityapartments.com/seattle/belltown/moda-apartments',
            cache_path=os.path.join(args.cache, 'Moda'),
        ),
        EquityScraper(
            name='Monterra in Mill Creek',
            url='http://www.equityapartments.com/seattle/mill-creek/monterra-in-mill-creek-apartments',
            cache_path=os.path.join(args.cache, 'Monterra_in_Mill_Creek'),
        ),
        EquityScraper(
            name='Odin',
            url='http://www.equityapartments.com/seattle/ballard/odin-apartments',
            cache_path=os.path.join(args.cache, 'Odin'),
        ),
        EquityScraper(
            name='Old Town Lofts',
            url='http://www.equityapartments.com/seattle/downtown-redmond/old-town-lofts-apartments',
            cache_path=os.path.join(args.cache, 'Old_Town_Lofts'),
        ),
        EquityScraper(
            name='Olympus',
            url='http://www.equityapartments.com/seattle/belltown/olympus-apartments',
            cache_path=os.path.join(args.cache, 'Olympus'),
        ),
        EquityScraper(
            name='Packard Building',
            url='http://www.equityapartments.com/seattle/capitiol-hill/packard-building-apartments',
            cache_path=os.path.join(args.cache, 'Packard_Building'),
        ),
        EquityScraper(
            name='Providence',
            url='http://www.equityapartments.com/seattle/bothell/providence-apartments',
            cache_path=os.path.join(args.cache, 'Providence'),
        ),
        EquityScraper(
            name='Red160',
            url='http://www.equityapartments.com/seattle/downtown-redmond/red160-apartments',
            cache_path=os.path.join(args.cache, 'Red160'),
        ),
        EquityScraper(
            name='Redmond Court',
            url='http://www.equityapartments.com/seattle/redmond/redmond-court-apartments',
            cache_path=os.path.join(args.cache, 'Redmond_Court'),
        ),
        EquityScraper(
            name='Rianna',
            url='http://www.equityapartments.com/seattle/capitol-hill/rianna-apartments',
            cache_path=os.path.join(args.cache, 'Rianna'),
        ),
        EquityScraper(
            name='Riverpark',
            url='http://www.equityapartments.com/seattle/downtown-redmond/riverpark-apartments',
            cache_path=os.path.join(args.cache, 'Riverpark'),
        ),
        EquityScraper(
            name='Seventh and James',
            url='http://www.equityapartments.com/seattle/first-hill/seventh-and-james-apartments',
            cache_path=os.path.join(args.cache, 'Seventh_and_James'),
        ),
        EquityScraper(
            name='Square One',
            url='http://www.equityapartments.com/seattle/roosevelt/square-one-apartments',
            cache_path=os.path.join(args.cache, 'Square_One'),
        ),
        EquityScraper(
            name='Surrey Downs',
            url='http://www.equityapartments.com/seattle/factoria/surrey-downs-apartments',
            cache_path=os.path.join(args.cache, 'Surrey_Downs'),
        ),
        EquityScraper(
            name='The Heights on Capitol Hill',
            url='http://www.equityapartments.com/seattle/capitol-hill/the-heights-on-capitol-hill-apartments',
            cache_path=os.path.join(args.cache, 'The_Heights_on_Capitol_Hill'),
        ),
        EquityScraper(
            name='The Pearl',
            url='http://www.equityapartments.com/seattle/capitiol-hill/the-pearl-apartments-capitol-hill',
            cache_path=os.path.join(args.cache, 'The_Pearl'),
        ),
        EquityScraper(
            name='The Reserve at Town Center',
            url='http://www.equityapartments.com/seattle/mill-creek/the-reserve-at-town-center-apartments',
            cache_path=os.path.join(args.cache, 'The_Reserve_at_Town_Center'),
        ),
        EquityScraper(
            name='Three20',
            url='http://www.equityapartments.com/seattle/capitol-hill/three20-apartments',
            cache_path=os.path.join(args.cache, 'Three20'),
        ),
        EquityScraper(
            name='Urbana',
            url='http://www.equityapartments.com/seattle/ballard/urbana-apartments',
            cache_path=os.path.join(args.cache, 'Urbana'),
        ),
        EquityScraper(
            name='Uwajimaya Village',
            url='http://www.equityapartments.com/seattle/international-district/uwajimaya-village-apartments',
            cache_path=os.path.join(args.cache, 'Uwajimaya_Village'),
        ),
        EquityScraper(
            name='Veloce',
            url='http://www.equityapartments.com/seattle/downtown-redmond/veloce-apartments',
            cache_path=os.path.join(args.cache, 'Veloce'),
        ),
    ]
    # pylint: enable=line-too-long

    status = args.func(
        args,
        [scraper for scraper in scrapers if re.search(args.scraper, scraper.name) is not None],
        connection,
    )
    connection.close()
    return status
