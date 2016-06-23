"""Library for Scraping Equity Apartments"""

import datetime
from html.parser import HTMLParser
import logging
import os

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
        HTMLParser.reset(self)


class EquityScraper(BaseScraper):

    """Web Scraper for Equity Apartments"""

    def cached_listings(self):
        """Generate a RentSurvey from the scrape cache."""
        parser = EquityParser()
        survey = None
        if self.cache_path is not None:
            survey = RentSurvey()
            for filename in sorted(os.listdir(self.cache_path)):
                timestamp = datetime.datetime.strptime(
                    os.path.splitext(filename)[0],
                    self.datetime_format,
                )
                path = os.path.join(self.cache_path, filename)
                with open(path, 'r', encoding=self.encoding) as f:
                    html = f.read()
                before = len(survey.listings)
                logging.debug('Parsing %s...', path)
                parser.reset()
                parser.feed(html)
                for unit in parser.units:
                    unit['timestamp'] = timestamp
                    unit['url'] = self.url
                    unit['unit'] = ' '.join([unit['building'], unit['unit']])
                    survey.listings.append(unit)
                if not len(survey.listings) > before:
                    logging.warning('%s is empty.', path)
            survey.listings.sort(key=lambda listing: listing['timestamp'])
            assert survey.is_valid()
        return survey

    def scrape_listings(self):
        """Scrape new RentSurvey from an Equity website."""

        user_agent = fake_useragent.UserAgent().random
        response, timestamp = self.scrape(headers={'User-Agent': user_agent})
        assert response.status_code == 200

        logging.debug('Parsing data scraped from %s...', self.url)
        parser = EquityParser()
        parser.feed(response.text)

        survey = RentSurvey()
        for unit in parser.units:
            unit['timestamp'] = timestamp
            unit['url'] = self.url
            unit['unit'] = ' '.join([unit['building'], unit['unit']])
            survey.listings.append(unit)
        assert survey.is_valid()
        return survey
