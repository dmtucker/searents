#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import print_function

import argparse
import datetime
import fake_useragent
import json
import os
import requests


def cli(parser=argparse.ArgumentParser()):
    parser.add_argument(
        "--newest",
        help="Specify the newest listings to include (requires -p).",
        )
    parser.add_argument(
        "--oldest",
        help="Specify the oldest listings to include (requires -p).",
        )
    parser.add_argument(
        "-f", "--floorplan",
        help="Print only units with the specified floorplan (requires -p).",
        )
    parser.add_argument(
        "-g", "--graphical",
        help="Print listings.json graphically.",
        default=False,
        action="store_true"
        )
    parser.add_argument(
        "-p", "--show-listings",
        help="Pretty print listings.json only.",
        default=False,
        action="store_true"
        )
    parser.add_argument(
        "-v", "--verbose",
        help="Print the gory details.",
        default=False,
        action="store_true"
        )
    return parser


def relative_path(path):
    """ Ensure relative paths work when this file is not in $PWD. """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


def scrape_data(url, timestamp=datetime.datetime.now()):
    data_file = relative_path(
        'scrapes/{0}.html'.format(timestamp).replace(' ', '_'),
        )
    try:
        with open(data_file, 'r') as f:
            raise Exception('SLOW DOWN!')
    except IOError as e:
        data = requests.get(
            url,
            headers={'User-Agent': fake_useragent.UserAgent().random},
            )
        with open(data_file, 'w') as f:
            f.write(data.text)
        return data.text, timestamp


def _get_urbana_floorplan(lines, offset):
    j = offset
    while ' <!--' not in lines[j]:
        if '<img' in lines[j]:
            return lines[j].split('alt="')[1].split('"')[0]
        j += 1


def _extract_listings_for_unit(listings, unit):
    extracted = []
    for listing in listings:
        if listing['unit'] == unit:
            extracted.append(listing)
    return extracted


def _all_units_in_listings(listings, sort=True, floorplan=None):
    units = []
    for listing in listings:
        if floorplan is None or listing['floorplan'][-1] in floorplan:
            if listing['unit'] not in units:
                units.append(listing['unit'])
    return sorted(units) if sort else units


def _filter_listings_by_age(listings, oldest=None, newest=None):
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


def _timestamp_to_datetime(timestamp):
    try:
        return datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        return datetime.datetime.strptime(timestamp, '%Y-%m-%d')


def _timestamp_to_float(timestamp):
    epoch = datetime.datetime(1970, 1, 1)
    return (_timestamp_to_datetime(timestamp)-epoch).total_seconds()


def _timestamps_to_plottable_dates(timestamps):
    return matplotlib.dates.date2num([
        datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
        for t in timestamps
        ])


def _price_to_float(price):
    return float(price.replace('$', '').replace(',', ''))


def _show_listings(listings, graphical=False, floorplan=None, sort=True):

    if graphical:
        all_units = _all_units_in_listings(
            listings,
            floorplan=floorplan,
            sort=sort,
            )
        color = iter(cm.rainbow(numpy.linspace(0, 1, len(all_units))))
        for unit in all_units:
            unit_listing = _extract_listings_for_unit(listings, unit)
            pyplot.plot_date(
                _timestamps_to_plottable_dates(
                    [l['timestamp'] for l in unit_listing],
                    ),
                [_price_to_float(l['price']) for l in unit_listing],
                'bo-',
                c=next(color),
                label='unit {0} ({1})'.format(
                    unit,
                    unit_listing[0]['floorplan'],
                    ),
                linewidth=2,
                )
            pyplot.text(
                _timestamps_to_plottable_dates([unit_listing[-1]['timestamp']]),
                _price_to_float(unit_listing[-1]['price']),
                'unit {0} ({1})'.format(unit, unit_listing[-1]['price']),
                )
        pyplot.title('Apartment Prices Over Time')
        pyplot.xlabel('Time')
        pyplot.ylabel('Price')
        pyplot.grid(b=True, which='major', color='k', linestyle='-')
        pyplot.grid(b=True, which='minor', color='k', linestyle=':')
        pyplot.minorticks_on()
        pyplot.legend(loc='best')
        pyplot.show()
    else:
        if sort:
            listings = sorted(listings, key=lambda k: k['unit'])
        for listing in listings:
            print(
                'timestamp: {0}, unit: {1}, price: {2}, floorplan: {3}'.format(
                    listing['timestamp'],
                    listing['unit'],
                    listing['price'],
                    listing['floorplan'],
                    ),
                )


def main(args):

    listings_file = relative_path('listings.json')
    if args.verbose:
        print('Reading {0}...'.format(listings_file))
    try:
        with open(listings_file, 'r') as f:
            listings = json.load(f)
    except IOError as e:
        if args.verbose:
            print('{0} does not exist.'.format(listings_file))
        listings = []
    if args.verbose:
        print('{0} listings were found.'.format(len(listings)))
    if args.show_listings:
        _show_listings(
            _filter_listings_by_age(
                listings,
                oldest=args.oldest,
                newest=args.newest,
                ),
            graphical=args.graphical,
            floorplan=args.floorplan,
            )
        return
    new_listings = []

    data, timestamp = scrape_data(
        'http://www.equityapartments.com/seattle/ballard/urbana-apartments',
        )
    if args.verbose:
        print('New data scraped at {0}.'.format(timestamp))
    lines = data.split('\n')
    if args.verbose:
        print('Parsing {0} lines...'.format(len(lines)))
    for i in range(len(lines)):
        line = lines[i]
        if '<!-- ledgerId' in line:
            if args.verbose:
                print('Unit found on line {0}: [{1}]'.format(i, line))
                print('\tunit: {0}'.format(line.split(' ')[-2]))
                print('Price found on line {0}: [{1}]'.format(i+7, lines[i+7]))
                print(
                    '\tprice: {0}'.format(
                        lines[i+7].split('>')[1].split('<')[0],
                        ),
                    )
                print(
                    'floorplan: {0}'.format(_get_urbana_floorplan(lines, i+1)),
                    )
            new_listings.append({
                'timestamp': str(timestamp),
                'unit': line.split(' ')[-2],
                'price': lines[i+7].split('>')[1].split('<')[0],
                'floorplan': _get_urbana_floorplan(lines, i+1),
                })

    if args.verbose:
        print('{0} new listings were found.'.format(len(new_listings)))
    _show_listings(
        new_listings,
        graphical=args.graphical,
        floorplan=args.floorplan,
        )
    listings += new_listings
    if args.verbose:
        print('Writing {0}...'.format(listings_file))
    with open(listings_file, 'w') as f:
        json.dump(listings, f)


if __name__ == '__main__':
    args = cli().parse_args()
    if args.graphical:
        import matplotlib
        from matplotlib import pyplot
        from matplotlib.pyplot import cm
        import numpy
    main(args)
