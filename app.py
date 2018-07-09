#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Oliver Zscheyge
Description:
    Web app that generates beautiful order documents for ePages shops.
"""

import os
from urllib.parse import urlparse

from flask import Flask, render_template, request, Response, abort, escape
import pdfkit
from app_installations import AppInstallations
from orders import get_orders, get_order, get_shop_logo_url

app = Flask(__name__)

ORDER_DB = {}
ORDERS_FOR_MERCHANT_KEY = ''
APP_INSTALLATIONS = None
DEFAULT_HOSTNAME = ''

@app.route('/')
def root():
    if DEFAULT_HOSTNAME != '':
        return render_template('index.html', installed=True, hostname=DEFAULT_HOSTNAME)
    return render_template('index.html', installed=False)


@app.route('/<hostname>')
def root_hostname(hostname):
    return render_template('index.html', installed=True, hostname=hostname)

@app.route('/callback')
def callback():
    args = request.args
    return_url = args.get("return_url")
    access_token_url = args.get("access_token_url")
    api_url = args.get("api_url")
    code = args.get("code")
    signature = args.get("signature")

    try:
        APP_INSTALLATIONS.retrieve_token_from_auth_code(api_url, code, access_token_url, signature)
    except Exception as e:
        print("token request failed with ", e)

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
        logo_url = get_shop_logo_url(api_url)

        orders = get_orders(AppInstallations.get_installation(hostname))
        return render_template('orderlist.html', orders=orders, logo=logo_url)
    except Exception as e:
        return \
u'''<h1>Something went wrong when fetching the order list! :(</h1>
<pre>
%s
</pre>
''' % escape(str(e)), 400


# Requires wkhtmltox or wkhtmltopdf installed besides Python's pdfkit
@app.route('/api/<hostname>/pdfs/<order_id>.pdf')
def pdf(hostname, order_id):
    order = get_order(AppInstallations.get_installation(hostname), order_id)
    filename = order_id + '.pdf'
    html_to_render = render_template('order_document.html', order=order)
    pdfkit.from_string(html_to_render,
                       filename, configuration=pdfkit.configuration(wkhtmltopdf="./bin/wkhtmltopdf"))
    pdffile = open(filename, "rb")
    response = Response(pdffile.read(), mimetype='application/pdf')
    pdffile.close()
    os.remove(filename)
    return response


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
           '127.0.0' in url or \
           '0.0.0.0:80' in url

@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404 File Not Found! :(</h1>', 404


def init():
    global APP_INSTALLATIONS
    global DEFAULT_HOSTNAME

    CLIENT_ID = os.environ.get('CLIENT_ID', '')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')
    API_URL = os.environ.get('API_URL', '')
    if API_URL != '':
        DEFAULT_HOSTNAME = urlparse(API_URL).hostname
    APP_INSTALLATIONS = AppInstallations(CLIENT_ID, CLIENT_SECRET)
    APP_INSTALLATIONS.retrieve_token_from_client_credentials(API_URL)

init()
if __name__ == '__main__':
    app.run()
