from .client import Client

# Create a global default client
_client = Client()

# Public API (shortcuts)
stream = _client.stream
def storage(name: str):
    return _client.storage(name)

# If users want, they can still manually import `Client` class
__all__ = ["Client", "stream", "storage"]
