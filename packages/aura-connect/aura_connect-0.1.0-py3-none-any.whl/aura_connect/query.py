import time
import threading
from typing import Callable, Any, List, Dict, Optional
from zenoh import Query, Querier, KeyExpr, Session


class QueryClient:
    """A simplified wrapper around Zenoh querying functionality."""

    def __init__(self, session, loop, key):
        """
        Initialize the query client.

        Args:
            session: Zenoh session object
            loop: Asyncio event loop
            key: The key to query on
        """
        self._session: Session = session
        self._loop = loop
        self._key: KeyExpr = key
        self._querier: Querier = None
        self._initialize()

    def _initialize(self):
        """Initialize the query client in the event loop."""

        # Use the synchronous API
        self._querier = self._session.declare_querier(self._key, timeout=1000)

    def query(
        self, value: Optional[bytes] = None, timeout_ms: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Send a query and get the responses.

        Args:
            value: Optional value to send with the query
            timeout_ms: Timeout in milliseconds

        Returns:
            A list of responses, each containing key and value
        """
        responses = []
        try:
            # Use the synchronous API
            replies = self._querier.get(payload=value)
            for reply in replies:
                key = reply.ok.key_expr
                value = reply.ok.payload.to_string()
                responses.append({"key": key, "value": value})
            return responses
        except TimeoutError:
            print(f"Query timed out after {timeout_ms} ms")
            return []
        except Exception as e:
            print(f"Query failed: {e}")


class QueryServer:
    """A simplified wrapper around Zenoh queryable functionality."""

    def __init__(self, session, loop, key, handler):
        """
        Initialize the query server.

        Args:
            session: Zenoh session object
            loop: Asyncio event loop
            key: The key to handle queries for
            handler: A callback function that takes (key, value) arguments and returns a response
        """
        self._session = session
        self._loop = loop
        self._key = key
        self._handler = handler
        self._queryable = None
        self._initialize()

    def _initialize(self):
        """Initialize the queryable in the event loop."""

        def _queryable_callback(query: Query):
            try:
                key = query.key_expr
                value = query.payload.to_string()

                print(f"Received query for key: {key}, value: {value}")
                # Call the handler to get the response
                response = self._handler(key, value)

                # Send the response back
                query.reply(self._key, response)
            except Exception as e:
                print(f"Error in queryable callback: {e}")

        # Use the synchronous API
        self._queryable = self._session.declare_queryable(
            self._key, _queryable_callback
        )

    def close(self):
        """Close the queryable."""
        if self._queryable:
            # Use the synchronous API
            self._queryable.undeclare()
            self._queryable = None

    def __del__(self):
        """Clean up resources when the object is deleted."""
        self.close()
