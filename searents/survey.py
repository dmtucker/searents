"""Structures for Tracking Listings"""

import datetime

import matplotlib
from matplotlib import pyplot
from matplotlib.pyplot import cm
import numpy


class RentSurvey(object):

    """
    A Collection of Listings

    Listings are dicts of the following form:
    {
        'price': float,
        'scraper': str,
        'timestamp': datetime.datetime,
        'unit': str,
        'url': str,
    }
    """

    def __init__(self, listings=None):
        self.listings = [] if listings is None else listings

    def __str__(self):
        return '\n'.join([
            '[{timestamp}] ${price:,.2f} {scraper} {unit}'.format(
                price=listing['price'],
                scraper=listing['scraper'],
                timestamp=listing['timestamp'],
                unit=listing['unit'],
            )
            for listing in self.listings
        ])

    def __eq__(self, survey):
        return all([
            hasattr(survey, 'listings'),
            len(self.listings) == len(survey.listings),
            all(
                survey_listing[key] == self_listing[key]
                for self_listing, survey_listing in zip(
                    sorted(self.listings, key=lambda listing: listing['timestamp']),
                    sorted(survey.listings, key=lambda listing: listing['timestamp']),
                )
                for key in ['price', 'scraper', 'timestamp', 'unit', 'url']
            ),
        ])

    def is_valid(self):
        """Verify all contained listings are well-formed."""
        for listing in self.listings:
            if not isinstance(listing['price'], float):
                return False
            if not isinstance(listing['scraper'], str):
                return False
            if not isinstance(listing['timestamp'], datetime.datetime):
                return False
            if not isinstance(listing['unit'], str):
                return False
            if not isinstance(listing['url'], str):
                return False
        return True

    def visualize(self, name=None):
        """Plot listings."""
        urls = set([listing['url'] for listing in self.listings])
        url_colors = iter(cm.rainbow(numpy.linspace(0, 1, len(urls))))  # pylint: disable=no-member
        for url in urls:
            url_listings = [listing for listing in self.listings if listing['url'] == url]
            url_color = next(url_colors)
            units = set([listing['unit'] for listing in url_listings])
            unit_colors =\
                iter(cm.rainbow(numpy.linspace(0, 1, len(units))))  # pylint: disable=no-member
            for unit in sorted(units):
                unit_listings = [listing for listing in url_listings if listing['unit'] == unit]
                unit_color = next(unit_colors)
                pyplot.plot_date(
                    matplotlib.dates.date2num([listing['timestamp'] for listing in unit_listings]),
                    [listing['price'] for listing in unit_listings],
                    'b-',
                    c=unit_color if len(urls) < 2 else url_color,
                    label=unit,
                    linewidth=2,
                )
                pyplot.text(
                    matplotlib.dates.date2num([unit_listings[-1]['timestamp']]),
                    unit_listings[-1]['price'],
                    '{0} ({1})'.format(unit, unit_listings[-1]['price']),
                )
        if name is not None:
            pyplot.gcf().canvas.set_window_title(name)
        pyplot.title('Apartment Prices Over Time')
        pyplot.xlabel('Time')
        pyplot.ylabel('Price')
        pyplot.grid(b=True, which='major', color='k', linestyle='-')
        pyplot.grid(b=True, which='minor', color='k', linestyle=':')
        pyplot.minorticks_on()
        pyplot.legend(loc='upper left', fontsize='xx-small')
        pyplot.show()
