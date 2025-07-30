import os
import time
import pytest
from litebaseio import Client, stream
from litebaseio.models import StreamEvent

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

def test_stream_on_emit(stream_client):
    received = []

    # Register an event handler
    @stream_client.on("test.sensor.temp")
    def handle(event: StreamEvent):
        received.append(event)

    # Start listening
    stream_client.start("test.sensor.temp", start_tx=0)

    # Emit an event
    emit_resp = stream_client.emit("test.sensor.temp", {"value": 42})
    assert emit_resp.count == 1

    # Give it some time to receive (since subscribe runs in background thread)
    time.sleep(2)

    # Verify
    assert len(received) >= 1
    assert isinstance(received[0], StreamEvent)
    assert "value" in received[0].data
    assert received[0].data["value"] == 42
