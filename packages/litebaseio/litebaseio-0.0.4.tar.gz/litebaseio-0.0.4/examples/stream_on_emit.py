import time
from litebaseio import stream

@stream.on('sensor.temp')
def handle_temperature(event):
    print(f"Temperature event received: {event.data}")

stream.start('sensor.temp')

stream.emit('sensor.temp', {"value": 26.5})

# Important: wait for event to arrive
time.sleep(2)
