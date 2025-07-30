import os
import pytest
from litebaseio import Client, storage
from litebaseio.models import StorageWriteResponse, StorageReadResponse

@pytest.fixture(scope="session")
def client() -> Client:
    api_key = os.getenv("LITE_API_KEY")
    base_url = os.getenv("LITE_BASE_URL", "https://api.litebase.io")
    if not api_key:
        pytest.fail("Missing LITE_API_KEY environment variable for E2E tests.")
    return Client(api_key=api_key, base_url=base_url)

@pytest.fixture
def store(client):
    return client.storage("test-storage")

def test_storage_set_and_get(store):
    key = "test:user:1001"
    value = b'{"name": "Alice"}'

    # Set a single key
    set_resp = store.set(key, value)
    assert isinstance(set_resp, StorageWriteResponse)
    assert set_resp.tx > 0

    # Get the key back
    result = store.get(key)
    assert isinstance(result, dict)
    assert result["name"] == "Alice"

def test_storage_batch_write_and_read(store):
    entries = [
        {"key": "test:user:1002", "value": {"name": "Bob"}},
        {"key": "test:user:1003", "value": {"name": "Charlie"}},
    ]

    # Batch write
    write_resp = store.write(entries)
    assert isinstance(write_resp, StorageWriteResponse)
    assert write_resp.tx > 0

    # Batch read
    keys = ["test:user:1002", "test:user:1003"]
    read_resp = store.read(keys)
    assert isinstance(read_resp, StorageReadResponse)
    assert read_resp.count == 2
    assert {r.key for r in read_resp.data} == set(keys)
    for record in read_resp.data:
        assert "name" in record.value

def test_storage_delete(store):
    key = "test:user:1004"
    value = b'{"name": "ToBeDeleted"}'

    # Set key first
    set_resp = store.set(key, value)
    assert set_resp.tx > 0

    # Delete the key
    delete_resp = store.delete(key)
    assert isinstance(delete_resp, StorageWriteResponse)
    assert delete_resp.tx > 0

    # Try getting the key back — should raise an error or not found
    with pytest.raises(Exception):
        _ = store.get(key)
