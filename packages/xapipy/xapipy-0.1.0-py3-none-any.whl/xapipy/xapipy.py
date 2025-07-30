import requests
from requests_oauthlib import OAuth1
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XApiPy:
    BASE_URL = "https://api.twitter.com/2"

    def __init__(self):
        """Initialize the X API v2 client with OAuth 1.0a credentials from .env."""
        load_dotenv(override=True)
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Missing OAuth 1.0a credentials in .env")
        self.auth = OAuth1(
            client_key=self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret
        )
        logger.info("XPyAPI initialized with OAuth 1.0a")

    def _make_request(self, method, endpoint, params=None, data=None):
        """Make an HTTP request to the X API."""
        url = f"{self.BASE_URL}{endpoint}"
        logger.debug("Request: %s %s, params=%s, data=%s", method, url, params, data)
        response = requests.request(
            method=method,
            url=url,
            auth=self.auth,
            params=params,
            json=data
        )
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error("HTTP Error: %s - %s", response.status_code, response.text)
            raise
        except ValueError:
            logger.error("Invalid JSON response: %s", response.text)
            raise

    def delete_tweet(self, tweet_id):
        """DELETE /2/tweets/:id"""
        return self._make_request("DELETE", f"/tweets/{tweet_id}")

    def get_tweets(self, tweet_ids=None, query=None, **params):
        """GET /2/tweets"""
        if tweet_ids:
            params["ids"] = ",".join(map(str, tweet_ids))
        if query:
            params["query"] = query
        return self._make_request("GET", "/tweets", params=params)

    def get_tweet(self, tweet_id, **params):
        """GET /2/tweets/:id"""
        return self._make_request("GET", f"/tweets/{tweet_id}", params=params)

    def post_tweet(self, text, **data):
        """POST /2/tweets"""
        data["text"] = text
        return self._make_request("POST", "/tweets", data=data)

    def post_like(self, user_id, tweet_id):
        """POST /2/users/:id/likes"""
        return self._make_request("POST", f"/users/{user_id}/likes", data={"tweet_id": tweet_id})

    def post_retweet(self, user_id, tweet_id):
        """POST /2/users/:id/retweets"""
        return self._make_request("POST", f"/users/{user_id}/retweets", data={"tweet_id": tweet_id})

    def get_user_by_username(self, username, **params):
        """GET /2/users/by/username/:username"""
        return self._make_request("GET", f"/users/by/username/{username}", params=params)

    def get_me(self, **params):
        """GET /2/users/me"""
        return self._make_request("GET", "/users/me", params=params)

    def get_spaces(self, **params):
        """GET /2/spaces"""
        return self._make_request("GET", "/spaces", params=params)

    def get_usage(self):
        """GET /2/usage/tweets"""
        return self._make_request("GET", "/usage/tweets")

    def get_trends_by_woeid(self, woeid, **params):
        """GET /2/trends/by/woeid/:id"""
        return self._make_request("GET", f"/trends/by/woeid/{woeid}", params=params)

    def get_personalized_trends(self, **params):
        """GET /2/users/personalized_trends"""
        return self._make_request("GET", "/users/personalized_trends", params=params)