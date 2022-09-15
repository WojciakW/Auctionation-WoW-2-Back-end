"""
Blizzard API and database connection resources.
"""

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import Timeout

import json
import psycopg2

from .local_settings import CLIENT_ID, CLIENT_SECRET, USER, PASSWORD


class BlizzApi:

    def __init__(self, url):
        self.url = url
        self.timeout = False
        self.response = None
        self.token = self.get_token()
    
    @staticmethod
    def get_token():
        """
        Returns Blizzard OAuth token.

        Requires Blizzard API client pre-setup and already generated client ID, Secret.
        """
        access_response = requests.post(
            'https://us.battle.net/oauth/token',
            auth=HTTPBasicAuth(
                CLIENT_ID,
                CLIENT_SECRET
            ),
            params={
                'grant_type': 'client_credentials'
            }
        )

        token = json.loads(access_response.content).get('access_token')

        return token

    def get_response(self):
        """
        Makes an attempt to connect Blizzard API, fails in case connection hangs for too long.
        """
        try:
            result = requests.get(
                self.url + self.token,
                timeout=10
            )
            self.response = result
            self.timeout = False

        except Timeout:
            self.response = None
            self.timeout = True


class DatabaseConnection:

    def __init__(self):
        self.connection = self.get_connection()
    
    def get_connection(self):
        try:
            result = psycopg2.connect(
                database='auctionation2_test',
                user=USER,
                password=PASSWORD,
                host='127.0.0.1',
                port='5432'
            )

            return result

        except psycopg2.OperationalError:
            return None
