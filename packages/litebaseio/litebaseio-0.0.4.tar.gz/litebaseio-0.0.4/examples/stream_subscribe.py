import os
import litebaseio

litebaseio.api_key = os.getenv("LITE_API_KEY")
litebaseio.base_url = os.getenv("LITE_BASE_URL", "https://api.litebase.io")

# Subscribe to real-time stream
for event in litebaseio.stream.subscribe("sensor.temp", start_tx=0):
    print(f"Received event: tx={event.tx} value={event.data}")
