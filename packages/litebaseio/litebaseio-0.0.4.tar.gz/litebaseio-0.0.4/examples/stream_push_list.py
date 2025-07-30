import os
from litebaseio import stream

# Push an event
push_resp = stream.push([
    {"stream": "sensor.temp", "data": {"value": 26.5}},
])
print(f"Pushed {push_resp.count} events")

# List recent events
events = stream.list("sensor.temp", limit=5)
for event in events:
    print(f"Event tx={event.tx}, value={event.data}")
