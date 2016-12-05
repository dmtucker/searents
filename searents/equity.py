"""Library for Scraping Equity Apartments"""

from html.parser import HTMLParser
import logging

import fake_useragent

from searents.scraper import BaseScraper
from searents.survey import RentSurvey


class EquityParser(HTMLParser):

    """Parse HTML from an Equity website."""

    units = []
    _unit = None

    def handle_startendtag(self, tag, attrs):
        if self._unit is not None:
            for attr in attrs:
                if attr[0] == 'src':
                    self._unit['floorplan'] = attr[1]
                if attr[0] == 'alt':
                    self._unit['description'] = attr[1]

    def handle_endtag(self, tag):
        if tag == 'li' and self._unit is not None:
            # End of Listing
            self.units.append(self._unit)
            self._unit = None

    def handle_data(self, data):
        data = data.strip()
        if len(data) > 0 and self._unit is not None:
            if self.get_starttag_text() == '<span class="pricing">':
                self._unit['price'] = float(data.replace('$', '').replace(',', ''))

    def handle_comment(self, data):
        data = data.strip()
        if data.startswith('ledgerId'):
            # Start of Listing
            ledger, building, unit = data.split(', ')
            self._unit = {
                'ledger': ledger.split(' ')[1],
                'building': building.split(' ')[1],
                'unit': unit.split(' ')[1],
            }

    def error(self, *args, **kwargs):
        pass

    def reset(self):
        self.units = []
        self._unit = None
        super().reset()


class EquityScraper(BaseScraper):

    """Web Scraper for Equity Apartments"""

    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url

    def survey(self, scrape, parser=EquityParser()):
        """Generate a RentSurvey from a Scrape."""
        parser.reset()
        parser.feed(scrape.text)
        survey = RentSurvey()
        for unit in parser.units:
            unit['timestamp'] = scrape.timestamp
            unit['url'] = scrape.url or self.url
            unit['unit'] = ' '.join([unit['building'], unit['unit']])
            survey.listings.append(unit)
        assert survey.is_valid()
        return survey

    def scrape_survey(self):
        """Scrape a RentSurvey from an Equity website."""
        return self.survey(
            self.scrape(self.url, headers={'User-Agent': fake_useragent.UserAgent().random})
        )

    @property
    def cache_survey(self):
        """Generate a RentSurvey from the Scrape cache."""
        assert self.cache_path is not None
        survey = RentSurvey()
        for scrape in self.cached_scrapes:
            listings = self.survey(scrape).listings
            if len(listings) < 1:
                logging.warning('%s is empty.', scrape.path)
            survey.listings.extend(listings)
        assert survey.is_valid()
        return survey
