"""Library for Scraping Equity Apartments"""

import datetime
import logging
import os

import fake_useragent

from searents.scraper import BaseScraper
from searents.survey import RentSurvey


class EquityScraper(BaseScraper):

    """Web Scraper for Equity Apartments"""

    @classmethod
    def parse(cls, html):
        """Parse HTML from an Equity website."""
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if '<!-- ledgerId' in line:

                unit = line.split(' ')[-2]
                logging.debug('Unit (%s) found on line %d: %s', unit, i, line.strip())

                price_i = i + 7
                price = float(
                    lines[price_i].split('>')[1].split('<')[0].replace('$', '').replace(',', '')
                )
                logging.debug(
                    'Price (%f) found on line %d: [%s]',
                    price,
                    price_i,
                    lines[price_i].strip(),
                )

                floorplan_i = i + 1
                while ' <!--' not in lines[floorplan_i]:
                    if '<img' in lines[floorplan_i]:
                        break
                    floorplan_i += 1
                floorplan = lines[floorplan_i].split('alt="')[1].split('"')[0]
                logging.debug(
                    'Floorplan (%s) found on line %d: [%s]',
                    floorplan,
                    floorplan_i,
                    lines[floorplan_i].strip(),
                )

                yield unit, price, floorplan

    def cached_listings(self):
        """Generate a RentSurvey from the scrape cache."""
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
                before = len(survey)
                logging.debug('Parsing %s...', path)
                for unit, price, floorplan in EquityScraper.parse(html=html):
                    survey.append({
                        'timestamp': timestamp,
                        'unit': unit,
                        'price': price,
                        'floorplan': floorplan,
                    })
                if not len(survey) > before:
                    logging.warning('%s is empty.', path)
            survey = RentSurvey(sorted(survey, key=lambda listing: listing['timestamp']))
            assert survey.is_valid()
        return survey

    def scrape_listings(self):
        """Scrape new RentSurvey from an Equity website."""

        user_agent = fake_useragent.UserAgent().random
        response, timestamp = self.scrape(headers={'User-Agent': user_agent})
        assert response.status_code == 200

        survey = RentSurvey()
        logging.debug('Parsing data scraped from %s...', self.url)
        for unit, price, floorplan in EquityScraper.parse(html=response.text):
            survey.append({
                'timestamp': timestamp,
                'unit': unit,
                'price': price,
                'floorplan': floorplan,
            })
        assert survey.is_valid()
        return survey
