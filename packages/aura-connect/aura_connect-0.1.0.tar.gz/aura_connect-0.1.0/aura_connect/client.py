import asyncio
import threading
import zenoh
from typing import Callable, Any, Dict, Optional
from .publisher import Publisher
from .subscriber import Subscriber
from .query import QueryClient, QueryServer


class AuraConnectClient:
    """
    A simplified wrapper around Zenoh SDK to make it easier to use without directly
    writing async code.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AuraConnect client with optional configuration.

        Args:
            config: Optional Zenoh configuration dictionary
        """
        self._config = config or zenoh.Config()
        self._session = None
        self._loop = None
        self._thread = None
        self._running = False
        self._publishers = {}
        self._subscribers = {}
        self._query_servers = {}
        self._query_clients = {}

        # Initialize and start the background event loop
        self._initialize()

    def _initialize(self):
        """Initialize the async event loop in a background thread."""
        self._loop = asyncio.new_event_loop()

        self._session = zenoh.open(self._config)
        self._running = True

        def _run_loop():
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(target=_run_loop, daemon=True)
        self._thread.start()

    def close(self):
        """Close the Zenoh session and stop the event loop."""
        if self._running:
            if self._session:
                # For newer Zenoh versions, close() is not an async function
                self._session.close()
            self._running = False

            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=1.0)

    def declare_publisher(self, key: str) -> Publisher:
        """
        Declare a publisher for the given key.

        Args:
            key: The key to publish on

        Returns:
            A Publisher object to publish data with
        """
        if key in self._publishers:
            return self._publishers[key]

        publisher = Publisher(self._session, self._loop, key)
        self._publishers[key] = publisher
        return publisher

    def declare_subscriber(
        self, key: str, handler: Callable[[str, bytes], None]
    ) -> Subscriber:
        """
        Declare a subscriber for the given key with a handler function.

        Args:
            key: The key to subscribe to
            handler: A callback function that takes (key, value) arguments

        Returns:
            A Subscriber object
        """
        if key in self._subscribers:
            return self._subscribers[key]

        subscriber = Subscriber(self._session, self._loop, key, handler)
        self._subscribers[key] = subscriber
        return subscriber

    def declare_query_server(
        self, key: str, handler: Callable[[str, bytes], bytes]
    ) -> QueryServer:
        """
        Declare a query server for the given key with a handler function.

        Args:
            key: The key to handle queries for
            handler: A callback function that takes (key, value) arguments and returns a response

        Returns:
            A QueryServer object
        """
        if key in self._query_servers:
            return self._query_servers[key]

        query_server = QueryServer(self._session, self._loop, key, handler)
        self._query_servers[key] = query_server
        return query_server

    def declare_query_client(self, key: str) -> QueryClient:
        """
        Declare a query client for the given key.

        Args:
            key: The key to query on

        Returns:
            A QueryClient object to make queries with
        """
        if key in self._query_clients:
            return self._query_clients[key]

        query_client = QueryClient(self._session, self._loop, key)
        self._query_clients[key] = query_client
        return query_client

    def __del__(self):
        """Clean up resources when the object is deleted."""
        self.close()
