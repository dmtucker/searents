"""General-Purpose Web Scraper"""

import datetime
import logging
import mimetypes
import os
from typing import Any, Iterator, Optional

import attr
import dateutil.parser
import requests


@attr.s(auto_attribs=True, kw_only=True)
class Scrape:  # pylint: disable=too-few-public-methods
    """Scraped Data and Associated Metadata"""

    text: str
    timestamp: datetime.datetime
    url: Optional[str]
    path: Optional[str]


class ScrapeError(Exception):
    """Scraping data failed."""


class BaseScraper:
    """Base Class for Searents Scrapers"""

    encoding = "utf-8"
    datetime_format = "%Y%m%dT%H%M%SZ.%f"

    def __init__(self, cache_path: Optional[str] = None) -> None:
        """Initialize cache_path."""
        self.cache_path = cache_path

    @property
    def cache_path(self) -> Optional[str]:
        """Get the path to the cache."""
        return self._cache_path

    @cache_path.setter
    def cache_path(self, path: Optional[str]) -> None:
        if path is not None:
            path = os.path.realpath(path)
            if not os.path.exists(path):
                os.makedirs(path)
            if not os.path.isdir(path):
                raise NotADirectoryError(path)
        self._cache_path = path  # pylint: disable=attribute-defined-outside-init

    def scrape(self, *args: Any, **kwargs: Any) -> Scrape:
        """GET a remote resource and save it."""
        try:
            response = requests.get(*args, **kwargs)
        except requests.exceptions.ConnectionError as exc:
            raise ScrapeError from exc
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise ScrapeError from exc
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
    def cached_scrapes(self) -> Iterator[Scrape]:
        """Load locally cached resources."""
        if self.cache_path is None:
            raise ValueError("cache_path is not set.")
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
                url=None,
                path=path,
            )
