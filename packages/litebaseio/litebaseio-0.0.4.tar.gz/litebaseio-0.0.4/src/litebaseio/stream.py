from typing import Any, Callable, Dict, List, Optional, Generator
import httpx
import threading

from .models import StreamPushResponse, StreamCommitResponse, StreamEvent

class Stream:
    """Litebase Stream client providing both event-driven and batch APIs."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self._handlers: Dict[str, List[Callable[[StreamEvent], None]]] = {}

    def emit(self, stream: str, data: Dict[str, Any]) -> StreamPushResponse:
        """Emit a single event to a stream.

        Args:
            stream: Stream name.
            data: Event payload.

        Returns:
            StreamPushResponse containing number of events committed.

        Example:
            stream.emit('sensor.temp', {"value": 25.5})
        """
        return self.push([{"stream": stream, "data": data}])

    def push(self, events: List[Dict[str, Any]]) -> StreamPushResponse:
        """Push multiple events into streams.

        Args:
            events: List of events with 'stream' and 'data'.

        Returns:
            StreamPushResponse containing number of events committed.

        Example:
            stream.push([
                {"stream": "sensor.temp", "data": {"value": 22.5}},
                {"stream": "sensor.humidity", "data": {"value": 45}},
            ])
        """
        response = self._client.post(
            "/v4/stream",
            json=events,
        )
        response.raise_for_status()
        return StreamPushResponse.model_validate(response.json())

    def on(self, stream: str) -> Callable[[Callable[[StreamEvent], None]], Callable[[StreamEvent], None]]:
        """Register an event handler for a stream.

        Args:
            stream: Stream name.

        Returns:
            A decorator to register the handler function.

        Example:
            @stream.on('sensor.temp')
            def handle(event):
                print(event.data)
        """
        def decorator(func: Callable[[StreamEvent], None]) -> Callable[[StreamEvent], None]:
            self._handlers.setdefault(stream, []).append(func)
            return func
        return decorator

    def start(self, stream: str, start_tx: Optional[int] = None) -> None:
        """Start subscribing to a stream and dispatch incoming events.

        Args:
            stream: Stream name to subscribe to.
            start_tx: (Optional) Starting transaction ID.

        Runs in a background thread.

        Example:
            stream.start('sensor.temp')
        """
        def _listen():
            params = {}
            if start_tx is not None:
                params["start_tx"] = start_tx

            with self._client.stream(
                "GET",
                f"/v4/stream/{stream}",
                params=params,
                timeout=None,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line and line.startswith("data:"):
                        payload = line[5:].strip()
                        event = StreamEvent.model_validate_json(payload)
                        self._dispatch(stream, event)

        threading.Thread(target=_listen, daemon=True).start()

    def _dispatch(self, stream: str, event: StreamEvent) -> None:
        for handler in self._handlers.get(stream, []):
            handler(event)

    def list(self, stream: str, start_tx: Optional[int] = None, end_tx: Optional[int] = None, limit: Optional[int] = None) -> List[StreamEvent]:
        """List committed transactions from a stream.

        Args:
            stream: Stream name.
            start_tx: (Optional) Start transaction ID.
            end_tx: (Optional) End transaction ID.
            limit: (Optional) Max number of events.

        Returns:
            List of StreamEvent objects.

        Example:
            events = stream.list("sensor.temp", limit=5)
        """
        params: Dict[str, Any] = {}
        if start_tx is not None:
            params["start_tx"] = start_tx
        if end_tx is not None:
            params["end_tx"] = end_tx
        if limit is not None:
            params["limit"] = limit

        response = self._client.get(
            f"/v4/stream/{stream}/events",
            params=params,
        )
        response.raise_for_status()

        raw = response.json() or []
        return [StreamEvent.model_validate(event) for event in raw]

    def get(self, stream: str, tx: int) -> Dict[str, Any]:
        """Retrieve a specific transaction payload.

        Args:
            stream: Stream name.
            tx: Transaction ID.

        Returns:
            Decoded event data.

        Example:
            event_data = stream.get("sensor.temp", 12345)
        """
        response = self._client.get(f"/v4/stream/{stream}/{tx}")
        response.raise_for_status()
        return response.json()

    def commit(self, stream: str, payload: bytes) -> StreamCommitResponse:
        """Commit a batch of events to a stream manually.

        Args:
            stream: Target stream name.
            payload: Binary payload to commit.

        Returns:
            StreamCommitResponse containing transaction ID.

        Example:
            stream.commit('sensor.temp', payload_bytes)
        """
        response = self._client.post(
            f"/v4/stream/{stream}",
            content=payload,
        )
        response.raise_for_status()
        return StreamCommitResponse.model_validate(response.json())
