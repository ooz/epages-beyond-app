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

from dto import get_shop_logo, \
                get_orders, \
                get_order_views, \
                get_order_extended_pdf_str, \
                orders_to_table


app = Flask(__name__)

CLIENT_ID = ''
CLIENT_SECRET = ''
API_URL = ''
CLIENT = None
ORDER_DB = {}
ORDERS_FOR_MERCHANT_KEY = ''


@app.route('/')
def root():
    if has_byd_credentials():
        return render_template('index.html', installed=True)
    return render_template('index.html', installed=False)
 
@app.route('/callback')
def callback():
    global API_URL
    args = request.args
    access_token, API_URL, return_url = epages.get_access_token(CLIENT_ID, CLIENT_SECRET, args)
    init_client()
    print('access_token: %s' % access_token)
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
""" % (return_url)

@app.route('/ui/orderlist')
def orderlist():
    try:
        logo_url = get_shop_logo(CLIENT)
        orders = get_orders(CLIENT)
        ORDER_DB[ORDERS_FOR_MERCHANT_KEY] = orders_to_table(CLIENT, orders)
        orders = get_order_views(CLIENT, orders)
        return render_template('orderlist.html', orders=orders, logo=logo_url)
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
        pdffile = open(filename)
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
    return 'epages-beyond-app.herokuapp.com' in url or \
           '.ngrok.io' in url or \
           'localhost:8080' in url or \
           '0.0.0.0:80' in url

@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404 File Not Found! :(</h1>', 404


def init():
    global CLIENT_ID
    global CLIENT_SECRET
    global API_URL
    global CLIENT
    global ORDER_DB

    CLIENT_ID = os.environ.get('CLIENT_ID', '')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')
    API_URL = os.environ.get('API_URL', '')

    init_client()

    ORDER_DB = {}

    assert has_client_credentials_or_private_app_credentials(), \
        'Please set either CLIENT_ID and CLIENT_SECRET and API_URL as environment variables!'

def init_client():
    global CLIENT
    global ORDERS_FOR_MERCHANT_KEY
    CLIENT = epages.BYDClient(API_URL, CLIENT_ID, CLIENT_SECRET)
    ORDERS_FOR_MERCHANT_KEY = API_URL

def has_client_credentials_or_private_app_credentials():
    return has_client_credentials()
def has_client_credentials():
    return CLIENT_ID != '' and CLIENT_SECRET != ''
def has_byd_credentials():
    return API_URL != '' and has_client_credentials()


init()
if __name__ == '__main__':
    app.run()
