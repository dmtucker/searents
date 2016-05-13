"""Structures for Tracking Listings"""

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
        'floorplan': str,
    }
    """

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
        return json.dumps(self, indent=4, sort_keys=True)

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
        for unit in sorted(units):
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
