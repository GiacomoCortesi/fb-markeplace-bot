import re

from splinter import Browser
from bs4 import BeautifulSoup as soup
import time
import logging

city_dict = {('48013', 'IT'): '103824622989212', ('48015', 'IT'): '105762946124194', ('02020', 'IT'): '103740509665061',
             ('17464', 'ES'): '104804759555744', ('7950', 'BE'): '112565218760518', ('34290', 'FR'): '105958486102381',
             ('48017', 'IT'): '109272745759400', ('48033', 'IT'): '108326449189280', ('48018', 'IT'): '103758862995533',
             ('48034', 'IT'): '107403715948727', ('27004', 'ES'): '109317799086039', ('48022', 'IT'): '110105015674078',
             ('305500', 'RO'): '110292358990034', ('27611', 'ES'): '108204459201292',
             ('33420', 'ES'): '106540879380410', ('27460', 'ES'): '106038869434965', ('27320', 'ES'): '112340842112389',
             ('27836', 'ES'): '113166662030293', ('48121', 'IT'): '115401551805737', ('48122', 'IT'): '112979228721001',
             ('48125', 'IT'): '112061362152513', ('48027', 'IT'): '111752902175169'}


def crawl(url: str, title_regex=''):
    crawl_result = {}

    # Set up Splinter
    browser = Browser('firefox', headless=True)

    browser.visit(url)
    time.sleep(3)

    # Parse the HTML
    html = browser.html

    # Create a BeautifulSoup object from the scraped HTML
    market_soup = soup(html, 'html.parser')
    # Check if HTML was scraped correctly
    browser.quit()

    # strip out dialogs from html data
    dialog_div = market_soup.find_all('div', {"role": "dialog"})
    _ = [dialog.extract() for dialog in dialog_div]

    # Extract product title
    titles_span = market_soup.find_all('span', {"class": "x1lliihq x6ikm8r x10wlt62 x1n2onr6"})
    titles_list = [title.text.strip() for title in titles_span]

    # Extract product price
    prices_span = market_soup.find_all('span',
                                       {
                                           "class": "x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x676frb x1lkfr7t x1lbecb7 x1s688f xzsf02u"})
    prices_list = [price.text.strip() for price in prices_span]

    locations_span = market_soup.find_all('span',
                                          {"class": "x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1j85h84"})
    locations_list = [location.text.strip() for location in locations_span]

    product_links = market_soup.find_all('a', {
        "class": "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1lku1pv"})
    product_links_list = [product_link.get('href') for product_link in product_links]

    if not (len(prices_span) == len(titles_span) and len(prices_span) == len(locations_span) and len(
            prices_span) == len(product_links)):
        crawl_result["ok"] = False
        return crawl_result

    products = []
    for title, price, location, link in zip(titles_list, prices_list, locations_list, product_links_list):
        products.append({"name": title,
                         "price": price,
                         "location": location,
                         "link": link
                         })

    if title_regex:
        filtered_products = []
        for product in products:
            m = re.match(title_regex, product["name"], re.IGNORECASE)
            if m:
                filtered_products.append(product)
        products = filtered_products

    crawl_result["products"] = products
    crawl_result["ok"] = True







    logging.info("crawl_result: {}".format(crawl_result))

    return crawl_result
