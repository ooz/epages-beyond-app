# -*- coding: utf-8 -*-
from flask import escape
import requests
import re


def get_orders(installation):
    return [OrderListItem(order, installation.hostname)
              for order
              in requests.get(installation.api_url + "/orders", headers={"AUTHORIZATION": "Bearer %s" % installation.access_token}).json().get("_embedded").get("orders")]

def get_order(installation, order_id):
    order_json = requests.get(installation.api_url + "/orders/%s" % order_id,
                 headers={"AUTHORIZATION": "Bearer %s" % installation.access_token}).json()
    shop_logo = get_shop_logo_url(installation.api_url)
    shop_json = requests.get(installation.api_url + "/shop").json()
    shop_json["logo_url"] = shop_logo
    return Order(order_json, shop_json, installation.hostname)

def get_shop_logo_url(api_url):

    shop_images = requests.get(api_url + "/shop/images").json()
    shop_images = [img for img \
                   in shop_images.get('_embedded', {}).get('images', []) \
                   if img.get('label', '') == 'logo']
    logo_url = ''
    if shop_images:
        logo_url = shop_images[0].get('_links', {}).get('data', {}).get('href', '')
    # Hack to remove image link template params
    logo_url = re.sub(r'\{.*\}', '', logo_url)
    logo_url += '&height=128'
    return logo_url

class OrderListItem(object):

    def __init__(self, order, hostname):
        billing_address = order.get('billingAddress')
        grand_total = order.get("grandTotal")

        self.pdf_link = '/api/%s/pdfs/%s.pdf' % (hostname, order.get("_id"))
        self.order_number = order.get("orderNumber")
        self.customer = escape('%s %s' % (billing_address.get('firstName', ''),
                                          billing_address.get('lastName', '')))
        self.grand_total = "%s %s" % (grand_total.get("amount"), grand_total.get("currency"))

class Order(OrderListItem):
    def __init__(self, order, shop, hostname):
        super().__init__(order, hostname)

        self.shop_name = escape(shop.get('name', ''))
        self.shop_email = shop.get('address', {}).get('email', '')
        self.logo_url = shop.get("logo_url", "")
        billing_address = order.get('billingAddress')
        self.billing_name = escape(self.customer)
        self.billing_street = escape('%s %s' % (billing_address.get('street', ''),
                                                billing_address.get('houseNumber', '')))
        self.billing_postcode = escape(billing_address.get('postalCode', ''))
        self.billing_town = escape(billing_address.get('city', ''))
        self.products = []