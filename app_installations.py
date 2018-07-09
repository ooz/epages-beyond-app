import base64
import hashlib
import hmac
from datetime import date, timedelta
from urllib.parse import urlparse
import requests

class AppInstallations(object):

    installations = {}

    def __init__(self, client_id, client_secret):
        self.client_secret = client_secret
        self.client_id = client_id

    def retrieve_token_from_auth_code(self, api_url, auth_code, token_url, signature):

        assert api_url != '' and auth_code != '' and token_url != '' and signature != ''

        #calculated_signature = self._calculate_signature(auth_code, token_url, self.client_secret)
        #assert signature == calculated_signature, "signature invalid - found %s but expected %s" % (signature, calculated_signature)

        params = {
            'grant_type': 'authorization_code',
            'code': auth_code
        }
        response = requests.post(url=token_url, data=params, auth=(self.client_id, self.client_secret))
        print(response.text)
        token_response = response.json()
        print(token_response)
        installation = Installation(api_url=api_url,
                                    access_token=token_response.get('access_token'),
                                    refresh_token=token_response.get('refresh_token'),
                                    expiry_date=(date.today() + timedelta(seconds=token_response.get('expires_in'))))

        AppInstallations.installations[urlparse(api_url).hostname] = installation

        return installation.access_token

    def retrieve_token_from_client_credentials(self, api_url):

        assert api_url != ''
        params = {
            'grant_type': 'client_credentials'
        }
        token_response = requests.post(url=api_url + "/oauth/token",
                                   data=params,
                                   auth=(self.client_id, self.client_secret)).json()

        installation = Installation(api_url=api_url,
                                    access_token=token_response.get('access_token'),
                                    expiry_date=(date.today() + timedelta(seconds=token_response.get('expires_in'))))

        AppInstallations.installations[installation.hostname] = installation

        return installation.access_token

    def get_token(self, hostname):
        installation = AppInstallations.installations[hostname]
        if installation.is_expired():
            return self.retrieve_token_from_client_credentials(installation.api_url)
        return AppInstallations.installations[hostname].access_token

    def _calculate_signature(self, code, access_token_url, client_secret):
        message = '%s:%s' % (code, access_token_url)
        digest = hmac.new(client_secret.encode('utf-8'),
                          msg=message.encode('utf-8'),
                          digestmod=hashlib.sha1).digest()
        return base64.b64encode(digest).decode('utf-8')

    @staticmethod
    def get_api_url(hostname):
        return AppInstallations.installations[hostname].api_url

    @staticmethod
    def get_installation(hostname):
        return AppInstallations.installations[hostname]

class Installation(object):

    def __init__(self, api_url, access_token, refresh_token=None, expiry_date=None):
        self.api_url = api_url
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry_date = expiry_date
        self.hostname = urlparse(api_url).hostname

    def is_expired(self):
        return date.today() > (self.expiry_date - timedelta(minutes=15))