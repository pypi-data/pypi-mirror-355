import os
from litebaseio import storage

# Choose your storage namespace
store = storage("test-storage")

# Set a key
set_resp = store.set("example:user:1", b'{"name": "Alice"}')
print(f"Set key tx={set_resp.tx}")

# Get the key
value = store.get("example:user:1")
print("Get key value:", value)
