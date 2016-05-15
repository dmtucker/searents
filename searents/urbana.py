"""Library for Scraping Urbana Apartments"""

import datetime
import os

import fake_useragent

from searents.scraper import BaseScraper
from searents.survey import RentSurvey


class UrbanaScraper(BaseScraper):

    """Web Scraper for Urbana Apartments"""

    @classmethod
    def parse(cls, html, debug=False):
        """Parse HTML from Urbana's website."""
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if '<!-- ledgerId' in line:

                unit = line.split(' ')[-2]

                price_i = i + 7
                price = float(
                    lines[price_i].split('>')[1].split('<')[0].replace('$', '').replace(',', '')
                )

                floorplan_i = i + 1
                while ' <!--' not in lines[floorplan_i]:
                    if '<img' in lines[floorplan_i]:
                        break
                    floorplan_i += 1
                floorplan = lines[floorplan_i].split('alt="')[1].split('"')[0]

                if debug:
                    print('-' * 4)
                    print('Unit found on line {0}: [{1}]'.format(
                        i,
                        line.strip(),
                    ))
                    print('\tunit: {0}'.format(unit))
                    print('Price found on line {0}: [{1}]'.format(
                        price_i,
                        lines[price_i].strip(),
                    ))
                    print('\tprice: {0}'.format(price))
                    print('Floorplan found on line {0}: [{1}]'.format(
                        floorplan_i,
                        lines[floorplan_i].strip(),
                    ))
                    print('\tfloorplan: {0}'.format(floorplan))
                    print('-' * 4)

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
                for unit, price, floorplan in UrbanaScraper.parse(html=html):
                    survey.append({
                        'timestamp': timestamp,
                        'unit': unit,
                        'price': price,
                        'floorplan': floorplan,
                    })
                if self.verbose and not len(survey) > before:
                    print('* {0} is empty.'.format(path))
            survey = RentSurvey(sorted(survey, key=lambda listing: listing['timestamp']))
            assert survey.is_valid()
        return survey

    def scrape_listings(self):
        """Scrape new RentSurvey from Urbana's website."""

        url = 'http://www.equityapartments.com/seattle/ballard/urbana-apartments'
        user_agent = fake_useragent.UserAgent().random
        response, timestamp = self.scrape(url, headers={'User-Agent': user_agent})
        assert response.status_code == 200

        survey = RentSurvey()
        for unit, price, floorplan in UrbanaScraper.parse(html=response.text):
            survey.append({
                'timestamp': timestamp,
                'unit': unit,
                'price': price,
                'floorplan': floorplan,
            })
        assert survey.is_valid()
        return survey
