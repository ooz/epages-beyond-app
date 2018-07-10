import base64
import hashlib
import hmac
from datetime import date, timedelta
from urllib.parse import urlparse
import requests
import os
import psycopg2

class AppInstallations(object):

    def __init__(self, client_id, client_secret):
        self.client_secret = client_secret
        self.client_id = client_id
        self.installations = {}

    def retrieve_token_from_auth_code(self, api_url, auth_code, token_url, signature):
        """Retrieve a token using the auth code and initialize app installation data
        """
        assert api_url != '' and auth_code != '' and token_url != '' and signature != ''

        calculated_signature = self._calculate_signature(auth_code, token_url, self.client_secret)
        assert signature == calculated_signature, "signature invalid - found %s but expected %s" % (signature, calculated_signature)

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

        self.upsert_installation(installation)

        return installation.access_token

    def retrieve_token_from_client_credentials(self, api_url):
        """Retrieve a token using client credentials and initialize app installation data
        """
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

        self.upsert_installation(installation)

        return installation.access_token

    def _calculate_signature(self, code, access_token_url, client_secret):
        message = '%s:%s' % (code, access_token_url)
        digest = hmac.new(client_secret.encode('utf-8'),
                          msg=message.encode('utf-8'),
                          digestmod=hashlib.sha1).digest()
        return base64.b64encode(digest).decode('utf-8')

    def get_installation(self, hostname):
        return self.installations[hostname]
    
    def upsert_installation(self, installation):
        self.installations[installation.hostname] = installation
    
        
class PostgresAppInstallations(AppInstallations):
    
    def __init__(self, database_url, client_id, client_secret):
        super().__init__(client_id, client_secret)
        self.database_url = database_url

    def create_schema(self):
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor() as curs:
                curs.execute("""CREATE TABLE IF NOT EXISTS APP_INSTALLATIONS (
                              HOSTNAME varchar(255) UNIQUE NOT NULL,
                              API_URL varchar(255) NOT NULL,
                              ACCESS_TOKEN varchar(4096) NOT NULL,
                              REFRESH_TOKEN varchar(4096) NOT NULL,
                              EXPIRY_DATE timestamp NOT NULL
                            )""")

    def get_installation(self, hostname):
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM APP_INSTALLATIONS WHERE HOSTNAME=%s", (hostname,))
                entry = curs.fetchone()
                if entry:
                    print("Found installation for hostname %s" % hostname)
                    return Installation(api_url=entry[1],
                                 access_token=entry[2],
                                 refresh_token=entry[3],
                                 expiry_date=entry[4])
        return None

    def upsert_installation(self, installation):
        print("Upsert installation")
        sql = ''
        if self.get_installation(installation.hostname):
            print("Updating APP_INSTALLATIONS entry for %s" % installation.hostname)
            sql = "UPDATE APP_INSTALLATIONS SET API_URL=%s, ACCESS_TOKEN=%s, REFRESH_TOKEN=%s, EXPIRY_DATE=%s WHERE HOSTNAME=%s"
        else: 
            print("Creating APP_INSTALLATIONS entry for %s" % installation.hostname)
            sql = "INSERT INTO APP_INSTALLATIONS (API_URL, ACCESS_TOKEN, REFRESH_TOKEN, EXPIRY_DATE, HOSTNAME) VALUES(%s, %s, %s, %s, %s)"
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor() as curs:
                curs.execute(sql, (installation.api_url, installation.access_token, installation.refresh_token, installation.expiry_date, installation.hostname))


class Installation(object):

    def __init__(self, api_url, access_token, refresh_token=None, expiry_date=None):
        self.api_url = api_url
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry_date = expiry_date
        self.hostname = urlparse(api_url).hostname

    def is_expired(self):
        return date.today() > (self.expiry_date - timedelta(minutes=15))