import asyncio
from typing import Any, Union


class Publisher:
    """A simplified wrapper around Zenoh publisher."""

    def __init__(self, session, loop, key):
        """
        Initialize the publisher.

        Args:
            session: Zenoh session object
            loop: Asyncio event loop
            key: The key to publish on
        """
        self._session = session
        self._loop = loop
        self._key = key

    def put(self, value: Union[str, bytes, dict, Any]):
        """
        Publish a value on the publisher's key.

        Args:
            value: The value to publish (will be converted to bytes if needed)
        """
        # Convert value to bytes if needed
        if isinstance(value, str):
            value_bytes = value.encode()
        elif isinstance(value, dict):
            import json

            value_bytes = json.dumps(value).encode()
        elif isinstance(value, bytes):
            value_bytes = value
        else:
            import pickle

            value_bytes = pickle.dumps(value)

        self._session.put(self._key, value_bytes)
