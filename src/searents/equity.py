"""Library for Scraping Equity Apartments"""

from html.parser import HTMLParser
import logging
from typing import Any, Dict, List, Optional, Tuple

from searents.scraper import BaseScraper, Scrape
from searents.survey import RentListing, RentSurvey


class EquityParser(HTMLParser):
    """Parse HTML from an Equity website."""

    units: List[Dict[str, str]] = []
    _unit: Optional[Dict[str, str]] = None

    def handle_startendtag(
        self,
        tag: str,
        attrs: List[Tuple[str, Optional[str]]],
    ) -> None:
        """Parse the floorplan and description."""
        if self._unit is not None:
            for attr in attrs:
                if attr[0] == "src":
                    self._unit["floorplan"] = attr[1] or ""
                if attr[0] == "alt":
                    self._unit["description"] = attr[1] or ""

    def handle_endtag(self, tag: str) -> None:
        """Detect the end of the listing."""
        if tag == "li" and self._unit is not None:
            self.units.append(self._unit)
            self._unit = None

    def handle_data(self, data: str) -> None:
        """Parse the price."""
        data = data.strip()
        if data and self._unit is not None:
            if self.get_starttag_text() == '<span class="pricing">':
                self._unit["price"] = data

    def handle_comment(self, data: str) -> None:
        """Detect the start of a listing."""
        data = data.strip()
        if data.startswith("ledgerId"):
            ledger, building, unit = data.split(", ")
            self._unit = {
                "ledger": ledger.split(" ")[1],
                "building": building.split(" ")[1],
                "unit": unit.split(" ")[1],
            }

    def error(self, message: str) -> None:
        """Suppress errors."""

    def reset(self) -> None:
        """Erase parser state."""
        self.units = []
        self._unit = None
        super().reset()


class EquityScraper(BaseScraper):
    """Web Scraper for Equity Apartments"""

    default_parser = EquityParser()

    def __init__(self, name: str, url: str, *args: Any, **kwargs: Any) -> None:
        """Extend BaseScraper initialization."""
        super().__init__(*args, **kwargs)
        self.name = name
        self.url = url

    def survey(
        self,
        scrape: Scrape,
        parser: Optional[EquityParser] = None,
    ) -> RentSurvey:
        """Generate a RentSurvey from a Scrape."""
        if parser is None:
            parser = self.default_parser
        parser.reset()
        parser.feed(scrape.text)
        survey = RentSurvey()
        for unit in parser.units:
            # The following fields are not included:
            # - description
            # - floorplan
            # - ledger
            survey.listings.append(
                RentListing(
                    price=float(unit["price"].replace("$", "").replace(",", "")),
                    scraper=self.name,
                    timestamp=scrape.timestamp,
                    unit=" ".join([unit["building"], unit["unit"]]),
                    url=scrape.url or self.url,
                ),
            )
        return survey

    def scrape_survey(self) -> RentSurvey:
        """Scrape a RentSurvey from an Equity website."""
        return self.survey(self.scrape(self.url))

    @property
    def cache_survey(self) -> RentSurvey:
        """Generate a RentSurvey from the Scrape cache."""
        if self.cache_path is None:
            raise ValueError("cache_path is not set.")
        survey = RentSurvey()
        for scrape in self.cached_scrapes:
            listings = self.survey(scrape).listings
            if not listings:
                logging.warning("%s is empty.", scrape.path)
            survey.listings.extend(listings)
        return survey
