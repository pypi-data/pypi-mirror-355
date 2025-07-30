import os
from typing import Optional
import httpx

from .storage import Storage
from .stream import Stream

class Client:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        # Load config from arguments or environment variables
        self._api_key = api_key or os.getenv("LITE_API_KEY")
        self._base_url = base_url or os.getenv("LITE_BASE_URL", "https://api.litebase.io")

        if not self._api_key:
            raise ValueError(
                "Litebase API key not provided. "
                "Please pass api_key=... or set environment variable LITE_API_KEY."
            )

        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )

        self._stream = Stream(self._client)

    @property
    def stream(self) -> Stream:
        """Access Stream API."""
        return self._stream

    def storage(self, name: str) -> Storage:
        """Access Storage API for a specific namespace."""
        return Storage(self._client, name)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
