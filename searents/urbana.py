"""Library for Scraping Urbana Apartments"""

import os

import fake_useragent

from .scraper import BaseScraper
from .survey import RentSurvey


class UrbanaScraper(BaseScraper):

    """Web Scraper for Urbana Apartments"""

    def parse(self, html):
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

                if self.debug:
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


    def scrape_listings(self):
        """Scrape new listings from Urbana's website."""

        url = 'http://www.equityapartments.com/seattle/ballard/urbana-apartments'
        user_agent = fake_useragent.UserAgent().random
        if self.verbose:
            print('Scraping {0} as {1}...'.format(url, user_agent))
        response, timestamp = self.scrape(url, headers={'User-Agent': user_agent})
        assert response.status_code == 200

        if self.verbose:
            print('Parsing scraped HTML...')
        listings = RentSurvey()
        for unit, price, floorplan in self.parse(html=response.text):
            listings.append({
                'timestamp': timestamp,
                'unit': unit,
                'price': price,
                'floorplan': floorplan,
            })
        return listings
