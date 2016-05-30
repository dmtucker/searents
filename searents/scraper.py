"""General-Purpose Web Scraper"""

import datetime
import logging
import mimetypes
import os

import requests


class BaseScraper(object):

    """Base Class for Searents Scrapers"""

    encoding = 'utf-8'
    datetime_format = '%Y-%m-%d_%H:%M:%S.%f'

    def __init__(self, url, cache_path=None):
        self.url = url
        self.cache_path = cache_path

    @property
    def cache_path(self):
        """Get the path to the cache."""
        return self._cache_path

    @cache_path.setter
    def cache_path(self, path):
        if path is not None:
            path = os.path.realpath(path)
            if not os.path.exists(path):
                os.makedirs(path)
            if not os.path.isdir(path):
                raise NotADirectoryError(path)
        self._cache_path = path  # pylint: disable=attribute-defined-outside-init

    def scrape(self, headers=None, path=None):
        """GET a remote resource and save it."""
        logging.info('Scraping %s...', self.url)
        response = requests.get(self.url, headers=headers)
        timestamp = datetime.datetime.now()
        if path is None:
            path = self.cache_path
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
            logging.info('Saving scraped data to %s...', path)
            with open(path, 'w', encoding=self.encoding) as f:
                f.write(response.text)
        return response, timestamp
