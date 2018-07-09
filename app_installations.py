
from datetime import date, timedelta
from urllib.parse import urlparse
import requests

class AppInstallations(object):

    installations = {}

    def __init__(self, client_id, client_secret):
        self.client_secret = client_secret
        self.client_id = client_id

    def retrieve_token_from_auth_code(self, api_url, auth_code, token_url):

        assert api_url != '' and auth_code != '' and token_url != ''
        params = {
            'grant_type': 'code',
            'code': auth_code
        }
        token_response = requests.post(url=token_url,
                                   data=params,
                                   auth=(self.client_id, self.client_secret) ).json()

        installation = _Installation(api_url=api_url,
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

        installation = _Installation(api_url=api_url,
                                     access_token=token_response.get('access_token'),
                                     expiry_date=(date.today() + timedelta(seconds=token_response.get('expires_in'))))

        AppInstallations.installations[urlparse(api_url).hostname] = installation

        return installation.access_token

    def get_token(self, hostname):
        installation = AppInstallations.installations[hostname]
        if installation.is_expired():
            return self.retrieve_token_from_client_credentials(installation.api_url)
        return AppInstallations.installations[hostname].access_token

    @staticmethod
    def get_api_url(hostname):
        return AppInstallations.installations[hostname].api_url

class _Installation(object):

    def __init__(self, api_url, access_token, refresh_token=None, expiry_date=None):
        self.api_url = api_url
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry_date = expiry_date

    def is_expired(self):
        return date.today() > (self.expiry_date - timedelta(minutes=15))