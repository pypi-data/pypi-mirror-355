"""
This module is the central point for initializing the http client,
and handling dependencies injection of the http client and eventual
api_keys, basic_auth_username, and basic_auth_password or url overrides.

It also abstracts the store logic for the api_key login and logout.
"""

from qcogclient.httpclient import HttpClient, init_client
from qcogclient.store import GET, get


class Initializer:
    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        basic_auth_username: str | None = None,
        basic_auth_password: str | None = None,
    ) -> None:
        # If we have an http client, we can use it straight away.

        if http_client:
            self.client = http_client
        elif basic_auth_username and basic_auth_password:
            self.client = init_client(
                basic_auth_username=basic_auth_username,
                basic_auth_password=basic_auth_password,
                base_url=base_url,
            )
        else:
            _api_key_ = api_key or self.api_key

            if not _api_key_:
                raise ValueError(
                    "No API key found. Either provide an API key or login first."
                )

            self.client = init_client(api_key=_api_key_, base_url=base_url)

    @property
    def api_key(self) -> str | None:
        """Retrieve the API key from the store"""
        partial_store = get({"api_key": GET})
        return partial_store.get("api_key", None)
