import os
from litebaseio import storage

# Choose your storage namespace
store = storage("test-storage")

# Batch write multiple keys
write_resp = store.write([
    {"key": "example:user:2", "value": {"name": "Bob"}},
    {"key": "example:user:3", "value": {"name": "Charlie"}},
])
print(f"Batch write tx={write_resp.tx}")

# Batch read the keys
read_resp = store.read(["example:user:2", "example:user:3"])
for record in read_resp.data:
    print(f"{record.key} -> {record.value}")
