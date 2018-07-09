#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Oliver Zscheyge
Description:
    Web app that generates beautiful order documents for ePages shops.
"""

import os

import epages
from flask import Flask, render_template, request, Response, abort, escape
import pdfkit
from app_installations import AppInstallations
import requests
import re

from dto import get_shop_logo, \
                get_orders, \
                get_order_views, \
                get_order_extended_pdf_str, \
                orders_to_table


app = Flask(__name__)

ORDER_DB = {}
ORDERS_FOR_MERCHANT_KEY = ''
APP_INSTALLATIONS = None


@app.route('/')
def root():
    return render_template('index.html', installed=True)

@app.route('/callback')
def callback():
    args = request.args
    #TODO add auth code flow
    return_url = ""
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>PythonDemo Callback</title>
</head>
<body>
<h1>Callback</h1>
<p>Thanks for installing PythonDemo App! Hit the "return" link below to return to your MBO/Commerce Cockpit</p>
<a href="%s">return</a>
</body>
</html>
""" % return_url

@app.route('/ui/<hostname>/orders')
def orderlist(hostname):
    try:
        api_url = AppInstallations.get_api_url(hostname)
        shop_images = requests.get(api_url + "/api/shop").json()
        shop_images = [img for img \
                       in shop_images.get('_embedded', {}).get('images', []) \
                       if img.get('label', '') == 'logo']

        logo_url = ''
        if shop_images:
            logo_url = shop_images[0].get('_links', {}).get('data', {}).get('href', '')
        # Hack to remove image link template params
        logo_url = re.sub(r'\{.*\}', '', logo_url)
        logo_url += '&height=128'

        #orders = get_orders(CLIENT)
        #ORDER_DB[ORDERS_FOR_MERCHANT_KEY] = orders_to_table(CLIENT, orders)
        #orders = get_order_views(CLIENT, orders)
        return render_template('orderlist.html', orders=[], logo=logo_url)
    except epages.RESTError as e:
        return \
u'''<h1>Something went wrong when fetching the order list! :(</h1>
<pre>
%s
</pre>
''' % escape(str(e)), 400

# Requires wkhtmltox or wkhtmltopdf installed besides Python's pdfkit
@app.route('/api/pdfs/<order_id>.pdf')
def pdf(order_id):
    orders_for_merchant = ORDER_DB.get(ORDERS_FOR_MERCHANT_KEY, {})
    if order_id in orders_for_merchant.keys():
        order = orders_for_merchant[order_id]
        filename = order_id + '.pdf'
        html_to_render = get_order_extended_pdf_str(CLIENT, order)
        pdfkit.from_string(html_to_render,
                           filename, configuration=pdfkit.configuration(wkhtmltopdf="./bin/wkhtmltopdf"))
        pdffile = open(filename, "rb")
        response = Response(pdffile.read(), mimetype='application/pdf')
        pdffile.close()
        os.remove(filename)
        return response
    abort(404)


@app.before_request
def limit_open_proxy_requests():
    """Security measure to prevent:
    http://serverfault.com/questions/530867/baidu-in-nginx-access-log
    http://security.stackexchange.com/questions/41078/url-from-another-domain-in-my-access-log
    http://serverfault.com/questions/115827/why-does-apache-log-requests-to-get-http-www-google-com-with-code-200
    http://stackoverflow.com/questions/22251038/how-to-limit-flask-dev-server-to-only-one-visiting-ip-address
    """
    if not is_allowed_request():
        print("Someone is messing with us:")
        print(request.url_root)
        print(request)
        abort(403)

def is_allowed_request():
    url = request.url_root
    return '.herokuapp.com' in url or \
           '.ngrok.io' in url or \
           'localhost:8080' in url or \
           '0.0.0.0:80' in url

@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404 File Not Found! :(</h1>', 404


def init():
    global APP_INSTALLATIONS

    CLIENT_ID = os.environ.get('CLIENT_ID', '')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')
    api_url = os.environ.get('API_URL', '')

    APP_INSTALLATIONS = AppInstallations(CLIENT_ID, CLIENT_SECRET)
    APP_INSTALLATIONS.retrieve_token_from_client_credentials(api_url)

init()
if __name__ == '__main__':
    app.run()
