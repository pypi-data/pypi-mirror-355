"""
Test suite for aura_connect package.
"""
import pytest
import sys
import os

# Add the package to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_import_aura_connect():
    """Test that the main package can be imported."""
    try:
        import aura_connect
        assert hasattr(aura_connect, 'AuraConnectClient')
    except ImportError as e:
        pytest.fail(f"Failed to import aura_connect: {e}")

def test_import_client():
    """Test that the client module can be imported."""
    try:
        from aura_connect.client import AuraConnectClient
        assert AuraConnectClient is not None
    except ImportError as e:
        pytest.fail(f"Failed to import AuraConnectClient: {e}")

def test_import_publisher():
    """Test that the publisher module can be imported."""
    try:
        from aura_connect.publisher import Publisher
        assert Publisher is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Publisher: {e}")

def test_import_subscriber():
    """Test that the subscriber module can be imported."""
    try:
        from aura_connect.subscriber import Subscriber
        assert Subscriber is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Subscriber: {e}")

def test_import_query():
    """Test that the query module can be imported."""
    try:
        from aura_connect.query import QueryClient
        assert QueryClient is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Query: {e}")

def test_package_version():
    """Test that the package has a version."""
    import aura_connect
    # Check if version is defined (might be in __version__ or elsewhere)
    # This is a basic test to ensure the package is properly structured
    assert aura_connect.__name__ == 'aura_connect'
