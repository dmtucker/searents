"""Web Scraper for Urbana Apartments"""

import os

import fake_useragent

from scraper import BaseScraper


def UrbanaScraper(BaseScraper):

    def __init__(self, verbose=False, debug=False):
        self.verbose = verbose
        self.debug = debug

    def parse(self, html):
        """Parse HTML from Urbana's website into unit listings."""
        listings = []
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if '<!-- ledgerId' in line:

                listing = {'unit': line.split(' ')[-2]}
                listings.append(listing)

                price_i = i + 7
                listing['price'] = float(
                    lines[price_i].split('>')[1].split('<')[0].replace('$', '').replace(',', '')
                )

                floorplan_i = i + 1
                while ' <!--' not in lines[floorplan_i]:
                    if '<img' in lines[floorplan_i]:
                        break
                    floorplan_i += 1
                listing['floorplan'] = lines[floorplan_i].split('alt="')[1].split('"')[0],

                if self.debug:
                    print('-' * 4)
                    print('Unit found on line {0}: [{1}]'.format(i, line.strip()))
                    print('\tunit: {0}'.format(listing['unit']))
                    print('Price found on line {0}: [{1}]'.format(
                        price_i,
                        lines[price_i].strip(),
                    ))
                    print('\tprice: {0}'.format(listing['price']))
                    print('Floorplan found on line {0}: [{1}]'.format(
                        floorplan_i,
                        lines[floorplan_i].strip(),
                    ))
                    print('\tfloorplan: {0}'.format(listing['floorplan']))
                    print('-' * 4)

        return listings

    def scrape_listings(dirpath=os.path.join(os.getcwd(), 'urbana_scrapes')):
        """Scrape new listings from Urbana's website."""

        if not os.path.exists(dirpath):
            if self.verbose:
                print('Creating directory at {0}...'.format(dirpath))
            os.mkdir(dirpath)

        url = 'http://www.equityapartments.com/seattle/ballard/urbana-apartments'
        user_agent = fake_useragent.UserAgent().random
        if self.verbose:
            print('Scraping {0} (as {1}) to {2}...'.format(url, user_agent, dirpath))
        response, timestamp = scrape(url, headers={'User-Agent': user_agent}, path=dirpath)
        assert response.status_code == 200

        if self.verbose:
            print('Parsing scraped HTML...')
        listings = self.parse(html=response.text)
        for listing in listings:
            listing['timestamp'] = timestamp
        return listings
