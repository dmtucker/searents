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


def _all_units_in_listings(listings, sort=True):
    units = []
    for listing in listings:
        if listing['unit'] not in units:
            units.append(listing['unit'])
    return sorted(units) if sort else units


def _timestamp_to_float(timestamp):
    t = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
    return (t-datetime.datetime(1970, 1, 1)).total_seconds()


def _timestamps_to_plottable_dates(timestamps):
    return matplotlib.dates.date2num([
        datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
        for t in timestamps
        ])


def _price_to_float(price):
    return float(price.replace('$', '').replace(',', ''))


def _show_listings(listings, graphical=False):
    if graphical:
        all_units = _all_units_in_listings(listings)
        color = iter(cm.rainbow(numpy.linspace(0, 1, len(all_units))))
        for unit in all_units:
            unit_listing = _extract_listings_for_unit(listings, unit)
            pyplot.plot(
                [_timestamp_to_float(l['timestamp']) for l in unit_listing],
                [_price_to_float(l['price']) for l in unit_listing],
                c=next(color),
                label='unit {0} ({1})'.format(
                    unit,
                    unit_listing[0]['floorplan'],
                    ),
                linewidth=2,
                )
            '''
            pyplot.plot_date(
                _timestamps_to_plottable_dates(
                    [l['timestamp'] for l in unit_listing],
                    ),
                [_price_to_float(l['price']) for l in unit_listing],
                c=next(color),
                label='unit {0} ({1})'.format(
                    unit,
                    unit_listing[0]['floorplan'],
                    ),
                linewidth=2,
                )
            '''
        pyplot.title('Apartment Prices Over Time')
        pyplot.xlabel('Time')
        pyplot.ylabel('Price')
        pyplot.grid(b=True, which='major', color='k', linestyle='-')
        pyplot.grid(b=True, which='minor', color='k', linestyle=':')
        pyplot.minorticks_on()
        pyplot.legend(loc='best')
        pyplot.show()
    else:
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
    try:
        with open(listings_file, 'r') as f:
            listings = json.load(f)
    except IOError as e:
        listings = []
    if args.show_listings:
        _show_listings(listings, graphical=args.graphical)
        return
    new_listings = []

    data, timestamp = scrape_data(
        'http://www.equityapartments.com/seattle/ballard/urbana-apartments',
        )
    lines = data.split('\n')
    for i in range(len(lines)):
        line = lines[i]
        if ' <!--' in line:
            new_listings.append({
                'timestamp': str(timestamp),
                'unit': line.split(' ')[-2],
                'price': lines[i+7].split('>')[1].split('<')[0],
                'floorplan': _get_urbana_floorplan(lines, i+1),
                })

    _show_listings(new_listings, graphical=args.graphical)
    listings += new_listings
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
