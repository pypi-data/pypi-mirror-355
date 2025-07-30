import asyncio
from typing import Callable
from zenoh import Sample


class Subscriber:
    """A simplified wrapper around Zenoh subscriber."""

    def __init__(self, session, loop, key, handler):
        """
        Initialize the subscriber.

        Args:
            session: Zenoh session object
            loop: Asyncio event loop
            key: The key to subscribe to
            handler: A callback function that takes (key, value) arguments
        """
        self._session = session
        self._loop = loop
        self._key = key
        self._handler = handler
        self._subscriber = None
        self._initialize()

    def _initialize(self):
        """Initialize the subscriber in the event loop."""

        def _subscriber_callback(sample: Sample):
            try:
                key = sample.key_expr
                value = sample.payload.to_string()
                # Call user handler in the main thread to avoid threading issues
                self._handler(key, value)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")

        self._subscriber = self._session.declare_subscriber(
            self._key, _subscriber_callback
        )

    def close(self):
        """Close the subscriber."""
        if self._subscriber:
            self._subscriber.undeclare()
            self._subscriber = None

    def __del__(self):
        """Clean up resources when the object is deleted."""
        self.close()
