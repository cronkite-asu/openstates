import re

from billy.scrape import NoDataForPeriod
from billy.scrape.legislators import LegislatorScraper, Legislator

import lxml.html
import urllib, urlparse

class ARLegislatorScraper(LegislatorScraper):
    state = 'ar'

    def scrape(self, chamber, term):
        if term != '2011-2012':
            raise NoDataForPeriod

        url = ('http://www.arkleg.state.ar.us/assembly/2011/2011R/Pages/'
               'LegislatorSearchResults.aspx?member=&committee=All&chamber=')

        with self.urlopen(url) as page:
            root = lxml.html.fromstring(page)

            for a in root.xpath('//table[@class="dxgvTable"] \
                                  /tr[contains(@class, "dxgvDataRow")] \
                                  /td[1] \
                                  /a'):
                member_url = url_fix(a.attrib['href'])
                self.scrape_member(chamber, term, member_url)

    def scrape_member(self, chamber, term, member_url):
        with self.urlopen(member_url) as page:
            root = lxml.html.fromstring(page)

            name_and_party = root.xpath('string(//td[@class="SiteNames"])').split()

            title = name_and_party[0]
            if title == 'Representative':
                chamber = 'lower'
            elif title == 'Senator':
                chamber = 'upper'

            full_name = ' '.join(name_and_party[1:-1])

            party = name_and_party[-1]
            if party == '(R)':
                party = 'Republican'
            elif party == '(D)':
                party = 'Democratic'

            img = root.xpath('//img[@class="SitePhotos"]')[0]
            photo_url = img.attrib['src']

            # Need to figure out a cleaner method for this later
            info_box = root.xpath('string(//table[@class="InfoTable"])')
            district = re.search(r'District(.+)\r', info_box).group(1)
            try:
                email = re.search(r'Email(.+)\r', info_box).group(1)
            except:
                email = None
            try:
                occupation = re.search(r'Occupation(.+)\r', info_box).group(1)
            except:
                occupation = None
            try:
                religion = re.search(r'Church Affiliation(.+)\r', info_box).group(1)
            except:
                religion = None
            try:
                veteran = re.search(r'Veteran(.+)\r', info_box).group(1)
            except:
                veteran = None

            leg = Legislator(term, chamber, district, full_name, party=party,
                             photo_url=photo_url, email=email,
                             occupation=occupation, religion=religion,
                             veteran=veteran)
            leg.add_source(member_url)

            self.save_legislator(leg)


def url_fix(s, charset='utf-8'):
    """http://stackoverflow.com/questions/120951/how-can-i-normalize-a-url-in-python"""
    if isinstance(s, unicode):
        s = s.encode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))
