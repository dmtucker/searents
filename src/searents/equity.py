"""Library for Scraping Equity Apartments"""

from html.parser import HTMLParser
import logging
from typing import Dict, List

from searents.scraper import BaseScraper
from searents.survey import RentSurvey


class EquityParser(HTMLParser):
    """Parse HTML from an Equity website."""

    units: List[Dict] = []
    _unit = None

    def handle_startendtag(self, tag, attrs):
        """Parse the floorplan and description."""
        if self._unit is not None:
            for attr in attrs:
                if attr[0] == "src":
                    self._unit["floorplan"] = attr[1]
                if attr[0] == "alt":
                    self._unit["description"] = attr[1]

    def handle_endtag(self, tag):
        """Detect the end of the listing."""
        if tag == "li" and self._unit is not None:
            self.units.append(self._unit)
            self._unit = None

    def handle_data(self, data):
        """Parse the price."""
        data = data.strip()
        if data and self._unit is not None:
            if self.get_starttag_text() == '<span class="pricing">':
                self._unit["price"] = float(data.replace("$", "").replace(",", ""))

    def handle_comment(self, data):
        """Detect the start of a listing."""
        data = data.strip()
        if data.startswith("ledgerId"):
            ledger, building, unit = data.split(", ")
            self._unit = {
                "ledger": ledger.split(" ")[1],
                "building": building.split(" ")[1],
                "unit": unit.split(" ")[1],
            }

    def error(self, message):
        """Suppress errors."""

    def reset(self):
        """Erase parser state."""
        self.units = []
        self._unit = None
        super().reset()


class EquityScraper(BaseScraper):
    """Web Scraper for Equity Apartments"""

    default_parser = EquityParser()

    def __init__(self, name, url, *args, **kwargs):
        """Extend BaseScraper initialization."""
        super().__init__(*args, **kwargs)
        self.name = name
        self.url = url

    def survey(self, scrape, parser=default_parser):
        """Generate a RentSurvey from a Scrape."""
        parser.reset()
        parser.feed(scrape.text)
        survey = RentSurvey()
        for unit in parser.units:
            unit["scraper"] = self.name
            unit["timestamp"] = scrape.timestamp
            unit["unit"] = " ".join([unit["building"], unit["unit"]])
            unit["url"] = scrape.url or self.url
            survey.listings.append(unit)
        if not survey.is_valid():
            raise RuntimeError("The survey is no longer valid!")
        return survey

    def scrape_survey(self):
        """Scrape a RentSurvey from an Equity website."""
        return self.survey(self.scrape(self.url))

    @property
    def cache_survey(self):
        """Generate a RentSurvey from the Scrape cache."""
        if self.cache_path is None:
            raise ValueError("cache_path is not set.")
        survey = RentSurvey()
        for scrape in self.cached_scrapes:
            listings = self.survey(scrape).listings
            if not listings:
                logging.warning("%s is empty.", scrape.path)
            survey.listings.extend(listings)
        if not survey.is_valid():
            raise RuntimeError("The survey is no longer valid!")
        return survey
