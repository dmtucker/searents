"""Structures for Tracking Listings"""

import copy
import datetime
import json

import matplotlib
from matplotlib import pyplot
from matplotlib.pyplot import cm
import numpy


class RentSurvey(list):

    """
    A Collection of Listings

    Listings are dicts of the following form:
    {
        'timestamp': datetime.datetime,
        'unit': str,
        'price': float,
        'url': str,
    }
    """

    encoding = 'utf-8'
    datetime_format = '%Y-%m-%d %H:%M:%S.%f'

    @classmethod
    def deserialize(cls, serialized):
        """Recreate a serialized RentSurvey."""
        listings = json.loads(serialized)
        for listing in listings:
            listing['timestamp'] = datetime.datetime.strptime(
                listing['timestamp'],
                cls.datetime_format,
            )
        return cls(listings)

    def serialize(self):
        """Generate a string that can be used to recreate a RentSurvey."""
        serializable = copy.deepcopy(self)
        for listing in serializable:
            listing['timestamp'] = listing['timestamp'].strftime(self.datetime_format)
        return json.dumps(serializable, indent=4, sort_keys=True)

    @classmethod
    def load(cls, path):
        """Read a serialized RentSurvey from a file."""
        with open(path, 'r', encoding=cls.encoding) as f:
            return cls.deserialize(f.read())

    def save(self, path):
        """Write a serialized RentSurvey to a file."""
        with open(path, 'w', encoding=self.encoding) as f:
            return f.write(self.serialize())

    def __str__(self):
        return '\n'.join([
            'timestamp: {0}, unit: {1}, price: {2}, url: {3}'.format(
                listing['timestamp'],
                listing['unit'],
                listing['price'],
                listing['url']
            )
            for listing in self
        ])

    def is_valid(self):
        """Verify all contained listings are well-formed."""
        for listing in self:
            if not isinstance(listing['timestamp'], datetime.datetime):
                return False
            if not isinstance(listing['unit'], str):
                return False
            if not isinstance(listing['price'], float):
                return False
            if not isinstance(listing['url'], str):
                return False
        return True

    def visualize(self, name=None):
        """Plot listings."""
        urls = set([listing['url'] for listing in self])
        url_colors = iter(cm.rainbow(numpy.linspace(0, 1, len(urls))))  # pylint: disable=no-member
        for url in urls:
            url_listings = [listing for listing in self if listing['url'] == url]
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
