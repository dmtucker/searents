"""General-Purpose Web Scraper"""

import datetime
import mimetypes
import os

import requests


class BaseScraper(object):  # pylint: disable=too-few-public-methods

    """Base Class for Searents Scrapers"""

    encoding = 'utf-8'
    datetime_format = '%Y-%m-%d_%H:%M:%S.%f'

    def __init__(self, cache=None, verbose=False, debug=False):
        self.cache = cache
        self.verbose = verbose
        self.debug = debug

    def scrape(self, url, headers=None, path=None):
        """GET a remote resource and save it."""
        response = requests.get(url, headers=headers)
        timestamp = datetime.datetime.now()
        if path is None:
            path = self.cache
            if not os.path.isdir(path):
                os.mkdir(path)
        if path is not None:
            if os.path.isdir(path):
                extension = mimetypes.guess_extension(
                    response.headers['content-type'].split(';')[0],
                    strict=False,
                )
                path = os.path.join(
                    path,
                    '{name}{extension}'.format(
                        name=timestamp.strftime(self.datetime_format),
                        extension='' if extension is None else extension,
                    ),
                )
            if self.verbose:
                print('Saving scrape to {0}...'.format(path))
            with open(path, 'w', encoding=self.encoding) as f:
                f.write(response.text)
        return response, timestamp
