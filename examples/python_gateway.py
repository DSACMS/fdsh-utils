"""FDSH gateway class."""

from urllib.parse import urljoin

import logging
import requests
import ssl
import uuid

from requests.adapters import HTTPAdapter


class HubGateway:

    def __init__(
        self,
        base_url,
        token_path,
        client_id,
        client_secret,
        client_cert_path,
        client_key_path,
        resolve=None,
        education_enrollment_path="/api/v1/education-enrollments",
    ):
        self.base_url = base_url
        self.token_path = token_path
        self.client_id = client_id
        self.client_secret = client_secret
        self.resolve = self._parse_resolve(resolve)
        self.education_enrollment_path = education_enrollment_path

        self._token = None
        self._session = requests.Session()
        self._session.cert = (client_cert_path, client_key_path)
        self._session.mount("https://", TLS1_2_Adapter(resolve_dict=self.resolve))

    def get_education_enrollment_v1(self, payload):
        """Get enrollment data from FDSH NSC API.

        Payload is a dictionary passed inside the nscRequest object, e.g.
        {
          "personGivenName": "Neil",
          "personSurName": "Martinsen-Burrell",
          "asOfDate": "1900-01-01",
          "termsAcceptedIndicator": True,
          "personBirthDate": "1999-01-01",
        }
        """
        return self._post(self.education_enrollment_path, {"nscRequest": payload})

    @property
    def access_token(self):
        """Return the access token if we have one, otherwise get one."""
        if self._token is not None:
            return self._token

        # make a request to get an access token
        uri = urljoin(self.base_url, self.token_path)
        # print("Getting token from ", uri)
        response = self._session.post(
            uri,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        # token is inside the response
        self._token = self._handle_response(response)["access_token"]
        return self._token

    @staticmethod
    def _handle_response(response):
        """Return the JSON contents of the response unless there was an error."""
        # print("Handling response: ", response.status_code, response.content)
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()

        if response.status_code == 401:
            # token might have expired, clear it
            self._token = None

        response.raise_for_status()

    def _post(self, url_path, data):
        """Post data in a JSON request to the specified path.

        The url_path is joined to self.base_url. `data` is a dictionary
        sent in the body of the JSON request.
        """
        uri = urljoin(self.base_url, url_path)
        request = requests.Request(
            url=uri,
            method="POST",
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "messageID": str(uuid.uuid4()),
            },
            json=data,
        )
        return self._execute(request)

    def _execute(self, request):
        """Handle a request on our specially configured TLS connection."""
        return self._handle_response(self._session.send(self._session.prepare_request(request)))

    @staticmethod
    def _parse_resolve(resolve_string):
        """Parse a string like impl.hub.cms.gov:8443:127.0.0.1.

        Returns None if the argument is false-y.
        """
        if not resolve_string:
            return None
        host, port, ip = resolve_string.split(":")

        return {host: {port: ip}}


class TLS1_2_Adapter(HTTPAdapter):
    """Force TLS version 1.2"""

    def __init__(self, *args, resolve_dict={}, **kwargs):
        """Override DNS resolution for one host.

        resolve_dict has a hostname as the key and the value is a mapping from
        port number to an IP address.
        """
        self.resolve_dict = resolve_dict
        super().__init__(*args, **kwargs)

    def get_connection(self, *args, **kwargs):
        conn = super().get_connection(*args, **kwargs)

        if conn.host in self.resolve_dict:
            # Save original hostname for SSL/SNI & validation
            conn.assert_hostname = conn.host
            conn.server_hostname = conn.host

            # Redirect the actual network destination socket to the IP
            conn.host = self.resolve_dict[conn.host][conn.port]
        return conn

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        # Restrict both min and max to TLS 1.2 to completely force it
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)
