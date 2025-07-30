# AuraConnect

A simplified wrapper around the Zenoh Python SDK that makes it easier to use without dealing with async code directly.

## Features

- Simple declarative API with synchronous interface
- Support for Publishers and Subscribers
- Support for Query-Reply pattern
- Handles all async code in the background

## Installation

### Prerequisites

- Python 3.10 or higher
- [Zenoh](https://zenoh.io/) dependencies

### Setting up a virtual environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS
source venv/bin/activate
# On Windows
# .\venv\Scripts\activate
```

### Install from source

```bash
cd aura_connect
# Install required dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Usage

### Basic Publisher/Subscriber

```python
from aura_connect import AuraConnectClient

# Create a client
client = AuraConnectClient()

# Define a handler for received messages
def handle_message(key, value):
    print(f"Received on {key}: {value}")

# Declare a publisher and a subscriber
publisher = client.declare_publisher("demo/topic")
subscriber = client.declare_subscriber("demo/topic", handle_message)

# Publish a message
publisher.put("Hello, Zenoh!")
```

### Query-Reply Pattern

```python
from aura_connect import AuraConnectClient

# Create a client
client = AuraConnectClient()

# Define a handler for queries
def handle_query(key, value):
    request = value.decode() if value else ""
    print(f"Received query on {key}: {request}")
    return f"Response to: {request}".encode()

# Declare query server and client
query_server = client.declare_query_server("demo/query", handle_query)
query_client = client.declare_query_client("demo/query")

# Send a query and get responses
responses = query_client.query("What's your status?".encode())
for response in responses:
    print(f"Response from {response['key']}: {response['value'].decode()}")
```

## Examples

See the `examples` directory for more complete examples:

- `basic_connect_example.py`: Demonstrates basic pub/sub and query-reply functionality

## Configuration

You can pass Zenoh configuration when creating the client:

```python
config = {
    "mode": "peer",
    "listen": ["tcp/localhost:7447"]
}
client = AuraConnectClient(config)
```

## Development

See the [Development Guide](docs/development_guide.md) for information on how to contribute to this project.
