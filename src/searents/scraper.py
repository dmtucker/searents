"""General-Purpose Web Scraper"""

import datetime
import logging
import mimetypes
import os

import dateutil.parser
import requests


class Scrape:  # pylint: disable=too-few-public-methods
    """Scraped Data and Associated Metadata"""

    def __init__(self, text, timestamp, url=None, path=None):
        """Initialize scraped (meta)data."""
        self.text = text
        self.timestamp = timestamp
        self.url = url
        self.path = path


class BaseScraper:
    """Base Class for Searents Scrapers"""

    encoding = "utf-8"
    datetime_format = "%Y%m%dT%H%M%SZ.%f"

    def __init__(self, cache_path=None):
        """Initialize cache_path."""
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

    def scrape(self, *args, **kwargs):
        """GET a remote resource and save it."""
        response, timestamp = (
            requests.get(*args, **kwargs),
            datetime.datetime.now(datetime.timezone.utc),
        )
        response.raise_for_status()
        path = None
        if self.cache_path is not None:
            path = os.path.join(
                self.cache_path,
                "{timestamp}{extension}".format(
                    timestamp=timestamp.strftime(self.datetime_format),
                    extension=mimetypes.guess_extension(
                        response.headers["content-type"].split(";")[0],
                        strict=False,
                    )
                    or "",
                ),
            )
            logging.info("Caching %s at %s...", response.request.url, path)
            with open(path, "w", encoding=self.encoding) as scrape_f:
                scrape_f.write(response.text)
        return Scrape(
            text=response.text,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            url=response.request.url,
            path=path,
        )

    @property
    def cached_scrapes(self):
        """Load locally cached resources."""
        assert self.cache_path is not None
        for filename in os.listdir(self.cache_path):
            path = os.path.join(self.cache_path, filename)
            with open(path, "r", encoding=self.encoding) as scrape_f:
                text = scrape_f.read()
            timestamp_str, microsecond_str = os.path.splitext(filename)[0].split(".")
            yield Scrape(
                text=text,
                timestamp=dateutil.parser.parse(timestamp_str).replace(
                    microsecond=int(microsecond_str),
                ),
                path=path,
            )
