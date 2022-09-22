from json import loads

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from Scrapy.items import AnswearItem
from Scrapy.spiders.utils import clean


class Parser:

    def product_care(self, response):
        return response.css('.ProductActive__descriptionParagraph__2DAC6 ::text').getall()

    def product_category(self, response):
        categories = response.css('.Breadcrumbs__breadcrumbsLink__7uQ4x ::text').getall()
        return categories[1: ]

    def product_gender(self, response):
        gender_category = self.product_category(response)
        raw_gender = ' '.join(gender_category).lower()

        if 'on' in raw_gender:
            return 'Male'
        elif 'ona' in raw_gender:
            return 'Female'
        elif 'dieťa' in raw_gender:
            return 'Unisex-Children'

        return 'Unisex-adults'

    def product_colour(self, raw_colour):
        colour = raw_colour['productCard']['product']['cardDetails']['colorVariants'][0]['color']['name']
        return colour

    def product_image_urls(self, response, raw_colour):
        urls = response.css('.Image__cardImage__3eRwk ::attr(src)').getall()
        return {self.product_colour(raw_colour): urls}

    def product_sizes(self, response):
        sizes = clean(response.css('script:contains("allSizes")::text').get())
        raw_size = loads(sizes)

        return raw_size

    def product_price(self, script):
        currency = script['offers']['priceCurrency']
        price = script['offers']['price']

        return price, currency

    def product_skus(self, script, raw_size):
        skus = {}
        common_sku = {}
        common_sku['colour'] = self.product_colour(raw_size)
        common_sku['currency'] = self.product_price(script)[1]
        common_sku['price'] = self.product_price(script)[0]

        size_options = raw_size['productCard']['product']['cardDetails']['allSizes']

        for size in size_options:
            sku = common_sku.copy()
            sku['out_of_Stock'] = 'out_of_stock' in size['variation']['availability'].lower()
            sku['size'] = size['name']
            skus[size['name']] = sku

        return skus

    def raw_product(self, response):
        raw_detail = loads(response.css('script:contains("sku")::text').get())
        return raw_detail

    def parse_items(self, response):
        item = AnswearItem()
        sizes = self.product_sizes(response)
        raw_details = self.raw_product(response)

        item['brand'] = raw_details['offers']['seller']['name']
        item['gender'] = self.product_gender(response)
        item['name'] = raw_details['name']
        item['retailer_sku'] = raw_details['sku']
        item['url'] = raw_details['offers']['url']

        item['care'] = self.product_care(response),
        item['category'] = self.product_category(response)
        item['description'] = raw_details['description']

        item['image_urls'] = self.product_image_urls(response, sizes)
        item['skus'] = self.product_skus(raw_details, sizes)

        yield item


class Crawler(CrawlSpider):
    name = 'answearspider'
    start_urls = ['https://answear.sk/']
    category_css = ['.CategoriesSection__menuLink__2i9n6', '.SubcategoriesMenu__subsectionListItemLink__3TYpr',
                '.SubcategoryAccordion__subcategoryAccordionLabel__3WCHv', '.ProductsPagination__paginationPageNumbersItem__KUwFD']

    rules = (
        Rule(LinkExtractor(restrict_css=category_css)),
        Rule(LinkExtractor(restrict_css='.ProductItem__productCardImageWrapper__2eewd '),
             callback=Parser().parse_items),
    )

