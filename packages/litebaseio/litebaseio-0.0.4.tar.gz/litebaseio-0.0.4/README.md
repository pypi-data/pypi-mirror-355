# litebase

Litebase Python SDK provides a modern, lightweight client for accessing Litebase's Storage and Stream APIs. It is designed for developers who require scalable, versioned key-value storage, high-throughput event streams, and real-time subscription capabilities, all with a clean Python experience.

## Installation

Install using uv for faster dependency management:

```bash
uv pip install litebase
```
or using pip:

```bash
pip install litebase
```

Litebase officially supports Python 3.8 and above.

## Quickstart

Litebase is designed for simplicity. A few lines of code are enough to get started.

### Storage API

```python
from litebaseio import storage

# Initialize a storage namespace
store = storage("my-storage")

# Set a single key
set_response = store.set("user:1", b'{"name": "Alice", "email": "alice@example.com"}')
print(f"Set operation transaction ID: {set_response.tx}")

# Retrieve a single key
user_data = store.get("user:1")
print("Retrieved user data:", user_data)

# Batch write multiple records
batch_response = store.write([
    {"key": "user:2", "value": {"name": "Bob", "email": "bob@example.com"}},
    {"key": "user:3", "value": {"name": "Charlie", "email": "charlie@example.com"}},
])
print(f"Batch write transaction ID: {batch_response.tx}")

# Batch read multiple records
read_response = store.read(["user:2", "user:3"])
for record in read_response.data:
    print(f"Key: {record.key}, Value: {record.value}")

# Check if a key exists
exists = store.head("user:1")
print("Key user:1 exists:", exists)

# Delete a key
delete_response = store.delete("user:1")
print(f"Deleted key user:1, transaction ID: {delete_response.tx}")
```

### Stream API

```python
from litebaseio import stream

# Push multiple events into a stream
push_response = stream.push([
    {"stream": "sensor.temperature", "data": {"value": 22.5}},
    {"stream": "sensor.temperature", "data": {"value": 23.1}},
])
print(f"Pushed {push_response.count} events to stream")

# List the most recent events from a stream
events = stream.list("sensor.temperature", limit=10)
for event in events:
    print(f"Transaction ID: {event.tx}, Data: {event.data}, Time: {event.time}")

# Retrieve a specific event by transaction ID
if events:
    tx_id = events[0].tx
    event_data = stream.get("sensor.temperature", tx=tx_id)
    print("Specific event data:", event_data)

# Subscribe to real-time events
print("Subscribing to real-time sensor.temperature updates:")
for event in stream.subscribe("sensor.temperature", start_tx=0):
    print(f"Received event: {event.data}")
    # Optionally break after first event for demo purposes
    break
```

Before running any examples, ensure you have set your API key:

```bash
export LITE_API_KEY="your-litebase-api-key"
export LITE_BASE_URL="https://api.litebase.io"  # Optional, defaults automatically
```

## Development

Clone the repository:

```bash
git clone https://github.com/litebaseio/litebase-py.git
cd litebase-py
```

Set up the development environment:

```bash
make install-dev
make test
```

Testing is based on real API interactions with a Litebase server. A valid Litebase API key is required to run the full test suite successfully.

## License

This project is licensed under the [MIT License](./LICENSE).

Litebase provides a reliable platform for structured and real-time data management, whether for analytics, IoT applications, mobile telemetry, or large-scale distributed systems. This SDK is intended to offer a minimal, efficient, and production-ready integration path for developers building modern applications.
