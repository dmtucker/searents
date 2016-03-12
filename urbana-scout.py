#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import print_function

import argparse
import datetime
import json
import os
import requests


def cli(parser=argparse.ArgumentParser()):
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
    data_file = relative_path('scrapes/{0}.html'.format(timestamp.date()))
    try:
        with open(data_file, 'r') as f:
            raise Exception('This has already been run today.')
    except IOError as e:
        data = requests.get(url).text
        with open(data_file, 'w') as f:
            f.write(data)
        return data, timestamp


def _get_urbana_floorplan(lines, offset):
    j = offset
    while ' <!--' not in lines[j]:
        if '<img' in lines[j]:
            return lines[j].split('alt="')[1].split('"')[0]
        j += 1


def _print_listings(listings):
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
        _print_listings(listings)
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

    _print_listings(new_listings)
    listings += new_listings
    with open(listings_file, 'w') as f:
        json.dump(listings, f)


if __name__ == '__main__':
    main(cli().parse_args())
