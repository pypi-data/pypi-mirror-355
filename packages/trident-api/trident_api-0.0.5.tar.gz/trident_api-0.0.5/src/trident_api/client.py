import requests
import logging

logger = logging.getLogger(__name__)

class TridentClient:
    def __init__(self, service, username, password):
        self.service = service
        self.username = username
        self.password = password
        self.secrets = {"username": username, "password": password}
        self.session = requests.Session()

    def _get_access_token(self):
        """Retrieve access token from the authentication endpoint."""
        try:
            response = self.session.post(f"{self.service}/auth/login", json=self.secrets)
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
            self.session.cookies.set("refresh_token", refresh_token)

            logger.debug("Successfully retrieved access token.")
            return access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving access token: {e}")
            raise Exception(f"Failed to retrieve access token.") from e

    def _refresh_token(self):
        """Refresh the access token using the refresh token."""
        refresh_token = self.session.cookies.get("refresh_token")
        if not refresh_token:
            logger.error("No refresh token available.")
            raise Exception("No refresh token available.")

        try:
            response = self.session.post(f"{self.service}/auth/refresh", json={"refresh_token": refresh_token})
            response.raise_for_status()

            token_data = response.json()
            new_access_token = token_data.get("access_token")

            self.session.headers.update({"Authorization": f"Bearer {new_access_token}"})
            logger.debug("Access token refreshed successfully.")
            return new_access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing access token: {e}")
            raise Exception(f"Failed to refresh access token. Response: {response.text}") from e

    def _ensure_auth(self):
        """Ensure an access token is available before making a request."""
        if not self.session.headers.get("Authorization"):
            self._get_access_token()

    def request(self, method, path, **kwargs):
        """Generic request handler with authentication and retry on token expiration."""
        self._ensure_auth()
        url = self.service + path

        try:
            logger.info(f"{method} request for {url}")
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 401:
                logger.warning("Token expired. Refreshing token...")
                self._refresh_token()
                return self.session.request(method, url, **kwargs)  # Retry with new token

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Failed request. Response: {response.text}") from e

    def post(self, path, data):
        return self.request("POST", path, json=data)
      
    def put(self, path, data):
        return self.request("PUT", path, json=data)

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def delete(self, path, params=None):
        return self.request("DELETE", path, params=params)
