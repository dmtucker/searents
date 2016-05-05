#!/usr/bin/env python3

"""Web Scraper for Urbana Apartments"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import datetime
import json
import os

import fake_useragent
import requests


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
        "--tmi",
        help="Print parsing details (ignored with -r).",
        default=False,
        action="store_true"
    )
    return parser


def _timestamp_to_datetime(timestamp):  # TODO Consider merging this into _filter_listings_by_age.
    try:
        return datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        return datetime.datetime.strptime(timestamp, '%Y-%m-%d')

def _filter_listings_by_age(listings, oldest=None, newest=None):  # TODO Implement filtering.
    if oldest is None and newest is None:
        return listings
    filtered = []
    if oldest is not None:
        oldest_datetime = _timestamp_to_datetime(oldest)
        for listing in listings:
            if _timestamp_to_datetime(listing['timestamp']) >= oldest_datetime:
                filtered.append(listing)
        listings = filtered
    if newest is not None:
        filtered = []
        newest_datetime = _timestamp_to_datetime(newest)
        for listing in listings:
            if _timestamp_to_datetime(listing['timestamp']) < newest_datetime:
                filtered.append(listing)
        listings = filtered
    return filtered


class Survey(list):

    """
    A Collection of Listings

    Listings are dicts of the following form:
    {
        'timestamp': datetime.datetime,
        'unit': str,
        'price': float,
        'floorplan': str,
    }
    """

    # TODO Sort survey based on sort_key.
    #for listing in sorted(self, key=lambda listing: listing[sort_key]) if sort else self:

    datetime_format = '%Y-%m-%d %H:%M:%S.%f'

    @classmethod
    def deserialize(cls, serialized):
        """Recreate a serialized Survey."""
        listings = json.loads(serialized)
        for listing in listings:
            listing['timestamp'] = datetime.datetime.strptime(
                listing['timestamp'],
                cls.datetime_format,
            )
        return cls(listings)

    def serialize(self):
        """Generate a string that can be used to recreate a Survey."""
        serializable = list(self)
        for listing in serializable:
            listing['timestamp'] = listing['timestamp'].strftime(self.datetime_format)
        return json.dumps(self, indent=4)

    def __str__(self):
        return '\n'.join([
            'timestamp: {0}, unit: {1}, price: {2}, floorplan: {3}'.format(
                listing['timestamp'],
                listing['unit'],
                listing['price'],
                listing['floorplan'],
            )
            for listing in self
        ])

    def visualize(self):
        """Plot a Survey."""
        units = set([listing['unit'] for listing in self])
        color = iter(cm.rainbow(numpy.linspace(0, 1, len(units))))  # pylint: disable=no-member
        for unit in units:
            unit_listings = [listing for listing in self if listing['unit'] == unit]
            pyplot.plot_date(
                matplotlib.dates.date2num([listing['timestamp'] for listing in unit_listings]),
                [listing['price'] for listing in unit_listings],
                'bo-',
                c=next(color),
                label='unit {0} ({1})'.format(
                    unit,
                    unit_listings[0]['floorplan'],
                    ),
                linewidth=2,
                )
            pyplot.text(
                matplotlib.dates.date2num([unit_listings[-1]['timestamp']]),
                unit_listings[-1]['price'],
                'unit {0} ({1})'.format(unit, unit_listings[-1]['price']),
                )
        pyplot.title('Apartment Prices Over Time')
        pyplot.xlabel('Time')
        pyplot.ylabel('Price')
        pyplot.grid(b=True, which='major', color='k', linestyle='-')
        pyplot.grid(b=True, which='minor', color='k', linestyle=':')
        pyplot.minorticks_on()
        pyplot.legend(loc='upper left', fontsize='x-small')
        pyplot.show()


def parsed_urbana_listings(html, timestamp):
    """Parse HTML from Urbana's website into unit listings."""
    listings = Survey()
    lines = html.split('\n')
    for i, line in enumerate(lines):
        if '<!-- ledgerId' in line:

            floorplan_i = i+1
            while ' <!--' not in lines[floorplan_i]:
                if '<img' in lines[floorplan_i]:
                    break
                floorplan_i += 1

            listing = {
                'timestamp': timestamp,
                'unit': line.split(' ')[-2],
                'price': float(
                    lines[i+7].split('>')[1].split('<')[0].replace('$', '').replace(',', ''),
                ),
                'floorplan': lines[floorplan_i].split('alt="')[1].split('"')[0],
            }
            listings.append(listing)

            if ARGS.tmi:
                print('-'*4)
                print('Unit found on line {0}: [{1}]'.format(i, line.strip()))
                print('\tunit: {0}'.format(listing['unit']))
                print('Price found on line {0}: [{1}]'.format(i+7, lines[i+7].strip()))
                print('\tprice: {0}'.format(listing['price']))
                print('Floorplan found on line {0}: [{1}]'.format(
                    floorplan_i,
                    lines[floorplan_i].strip(),
                ))
                print('\tfloorplan: {0}'.format(listing['floorplan']))
                print('-'*4)

    return listings


def get_new_listings(verbose=False, loc=os.getcwd()):
    """Scrape new listings from Urbana's website."""
    url = 'http://www.equityapartments.com/seattle/ballard/urbana-apartments'
    user_agent = fake_useragent.UserAgent().random
    if verbose:
        print('Scraping {0} as {1}...'.format(url, user_agent))
    response = requests.get(url, headers={'User-Agent': user_agent})
    assert response.status_code == 200

    html = response.text
    timestamp = datetime.datetime.now()

    html_file = os.path.join(loc, 'scrapes', '{0}.html'.format(timestamp).replace(' ', '_'))
    if verbose:
        print('Saving scraped HTML to {0}...'.format(html_file))
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)

    if verbose:
        print('Parsing scraped HTML...')
    return parsed_urbana_listings(html, timestamp)


def main(args):
    """Execute CLI commands."""

    survey = None
    if args.verbose:
        print('Reading {0}...'.format(args.file), end=' ')
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            survey = Survey.deserialize(f.read())
        if args.verbose:
            print('{0} listings'.format(len(survey)))
    except FileNotFoundError:
        if args.read_only:
            raise
        elif args.verbose:
            print('not found')
        survey = Survey()
    assert survey is not None

    if args.read_only:
        if args.graphical:
            survey.visualize()
        else:
            print(survey)
    else:

        if args.verbose:
            print('Getting new listings...')
        new_listings = get_new_listings(verbose=args.verbose, loc=os.path.dirname(args.file))

        if args.verbose:
            print('{0} new listings were found.'.format(len(new_listings)))
        print(new_listings)

        if args.verbose:
            print('Writing {0}...'.format(args.file))
        survey += new_listings
        with open(args.file, 'w', encoding='utf-8') as f:
            f.write(survey.serialize())


if __name__ == '__main__':
    ARGS = cli().parse_args()
    if ARGS.tmi:
        raise NotImplementedError()  # TODO
    if ARGS.graphical:
        # pylint: disable=wrong-import-position
        import matplotlib
        from matplotlib import pyplot
        from matplotlib.pyplot import cm
        import numpy
        # pylint: enable=wrong-import-position
    main(ARGS)
