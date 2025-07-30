from typing import Any, Dict, List, Optional
import httpx

from .models import StorageReadResponse, StorageWriteResponse


class Storage:
    """Litebase Storage API client for a specific namespace.

    Example:
        store = storage("test-storage")
        store.set("example:user:1", b'{"name": "Alice"}')
    """

    def __init__(self, client: httpx.Client, storage: str) -> None:
        self._client = client
        self._storage = storage

    def get(self, key: str, tx: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve the value of a key.

        Args:
            key: The key to retrieve.
            tx: (Optional) Transaction ID for versioned read.

        Returns:
            The decoded value associated with the key.

        Example:
            value = store.get("example:user:1")
        """
        params = {"key": key}
        if tx is not None:
            params["tx"] = tx
        response = self._client.get(
            f"/v4/storage/{self._storage}/key", params=params
        )
        response.raise_for_status()
        return response.json()

    def head(self, key: str, tx: Optional[int] = None) -> bool:
        """Check if a key exists.

        Args:
            key: The key to check.
            tx: (Optional) Transaction ID for versioned existence check.

        Returns:
            True if the key exists, False otherwise.

        Example:
            exists = store.head("example:user:1")
        """
        params = {"key": key}
        if tx is not None:
            params["tx"] = tx
        response = self._client.head(
            f"/v4/storage/{self._storage}/key", params=params
        )
        return response.status_code == 200

    def set(self, key: str, value: bytes) -> StorageWriteResponse:
        """Set or overwrite a key with a binary value.

        Args:
            key: The key to set.
            value: The binary content to store.

        Returns:
            StorageWriteResponse containing the transaction ID.

        Example:
            store.set("example:user:1", b'{"name": "Alice"}')
        """
        response = self._client.post(
            f"/v4/storage/{self._storage}/key",
            params={"key": key},
            content=value,
        )
        response.raise_for_status()
        return StorageWriteResponse.model_validate(response.json())

    def delete(self, key: str) -> StorageWriteResponse:
        """Delete a key.

        Args:
            key: The key to delete.

        Returns:
            StorageWriteResponse containing the transaction ID.

        Example:
            store.delete("example:user:1")
        """
        response = self._client.delete(
            f"/v4/storage/{self._storage}/key",
            params={"key": key},
        )
        response.raise_for_status()
        return StorageWriteResponse.model_validate(response.json())

    def read(self, keys: List[str], tx: Optional[int] = None) -> StorageReadResponse:
        """Batch read multiple keys.

        Args:
            keys: List of keys to retrieve.
            tx: (Optional) Transaction ID for versioned snapshot.

        Returns:
            StorageReadResponse containing the records.

        Example:
            result = store.read(["example:user:1", "example:user:2"])
        """
        payload: Dict[str, Any] = {"keys": keys}
        if tx is not None:
            payload["tx"] = tx
        response = self._client.post(
            f"/v4/storage/{self._storage}/read",
            json=payload,
        )
        response.raise_for_status()
        return StorageReadResponse.model_validate(response.json())

    def write(self, records: List[Dict[str, Any]]) -> StorageWriteResponse:
        """Batch write multiple records.

        Args:
            records: List of records, each with 'key' and 'value'.

        Returns:
            StorageWriteResponse containing the transaction ID.

        Example:
            store.write([
                {"key": "example:user:2", "value": {"name": "Bob"}},
                {"key": "example:user:3", "value": {"name": "Charlie"}},
            ])
        """
        response = self._client.post(
            f"/v4/storage/{self._storage}/write",
            json=records,
        )
        response.raise_for_status()
        return StorageWriteResponse.model_validate(response.json())
