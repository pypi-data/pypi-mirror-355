import os
import time
import pytest
from litebaseio import Client, stream
from litebaseio.models import StreamPushResponse, StreamEvent

@pytest.fixture(scope="session")
def client() -> Client:
    api_key = os.getenv("LITE_API_KEY")
    base_url = os.getenv("LITE_BASE_URL", "https://api.litebase.io")
    if not api_key:
        pytest.fail("Missing LITE_API_KEY environment variable for E2E tests.")
    return Client(api_key=api_key, base_url=base_url)

@pytest.fixture
def stream_client(client):
    return client.stream

def test_stream_push_and_list(stream_client):
    # Push an event
    result = stream_client.push([
        {"stream": "sensor.temp", "data": {"value": 25.5}},
    ])
    assert isinstance(result, StreamPushResponse)
    assert result.count == 1

    # Give it some time to receive (since subscribe runs in background thread)
    time.sleep(2)

    # List recent events
    events = stream_client.list("sensor.temp", limit=5)
    assert isinstance(events, list)
    assert len(events) >= 1
    assert isinstance(events[0], StreamEvent)
    assert hasattr(events[0], "tx")
    assert hasattr(events[0], "data")
    assert hasattr(events[0], "time")

def test_stream_get_event(stream_client):
    # Push an event to retrieve later
    result = stream_client.push([
        {"stream": "sensor.temp", "data": {"value": 30}},
    ])
    assert result.count == 1

    # List and get the latest tx
    events = stream_client.list("sensor.temp", limit=1)
    assert len(events) >= 1
    tx = events[0].tx

    # Get specific event by tx
    event_data = stream_client.get("sensor.temp", tx)
    assert isinstance(event_data, dict)
    assert "value" in event_data
