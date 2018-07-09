# -*- coding: utf-8 -*-

import requests

def get_orders(installation):
    return [OrderListItem.from_order_json(order, installation.hostname)
              for order
              in requests.get(installation.api_url + "/orders", headers={"AUTHORIZATION": "Bearer %s" % installation.access_token}).json().get("_embedded").get("orders")]


class OrderListItem(object):
    @staticmethod
    def from_order_json(order, hostname):
        billing_address = order.get('billingAddress')
        grand_total = order.get("grandTotal")
        return OrderListItem(id=order.get("_id"),
                             hostname=hostname,
                             order_number=order.get("orderNumber"),
                             customer=billing_address.get("firstName", "") + billing_address.get("lastName", ""),
                             grand_total="%s %s" % (grand_total.get("amount"), grand_total.get("currency")))

    def __init__(self, id, hostname, order_number, customer, grand_total ):
        self.pdf_link = '/api/%s/pdfs/%s.pdf' % (hostname, id)
        self.order_number = order_number
        self.customer = customer
        self.grand_total = grand_total
