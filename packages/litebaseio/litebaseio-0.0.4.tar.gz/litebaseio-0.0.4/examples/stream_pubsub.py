import sys
import time
import threading
from litebaseio import stream

def publish_loop():
    """Continuously publish events every 2 seconds."""
    count = 0
    while True:
        payload = {"value": 20 + count}
        response = stream.emit("test.sensor.temp", payload)
        print(f"[PUBLISH] Sent event: {payload}, server acknowledged {response.count} event(s)")
        count += 1
        time.sleep(2)

def subscribe_loop():
    """Subscribe and print received events."""

    @stream.on("test.sensor.temp")
    def handle(event):
        print(f"[SUBSCRIBE] Received event: tx={event.tx}, data={event.data}")

    stream.start("test.sensor.temp")
    # stream.run_forever()
    time.sleep(1000)


def main():
    if len(sys.argv) < 2:
        print("Usage: python stream_pubsub.py [pub|sub]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "pub":
        publish_loop()
    elif mode == "sub":
        subscribe_loop()
    else:
        print("Unknown mode:", mode)
        print("Usage: python stream_pubsub.py [pub|sub]")
        sys.exit(1)

if __name__ == "__main__":
    main()
