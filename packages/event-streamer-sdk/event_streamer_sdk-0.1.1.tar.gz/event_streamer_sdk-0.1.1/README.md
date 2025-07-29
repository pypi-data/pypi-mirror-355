# Event Streamer SDK

A Python SDK for interacting with the Event Streamer blockchain event monitoring service. This SDK provides a simple and powerful way to subscribe to blockchain events and receive them via HTTP webhooks or WebSocket connections.

## Features

- 🔗 **Simple API Client**: Easy subscription management with typed responses
- 🌐 **Dual Event Handling**: Support for both HTTP webhooks and WebSocket connections
- ✅ **Auto-confirmation**: Automatic event delivery confirmation
- 🔒 **Type Safety**: Full type hints and Pydantic model validation
- ⚡ **Async/Await**: Modern async Python patterns throughout
- 🎯 **Decorator Pattern**: Clean event handler registration
- 🛡️ **Error Handling**: Comprehensive error handling and retries
- 🔮 **Future-Ready**: Prepared for authentication when the service adds it

## Installation

```bash
pip install event-streamer-sdk
```

## Quick Start

### HTTP Webhook Example

```python
import asyncio
from event_poller_sdk import EventStreamer
from event_poller_sdk.models.subscriptions import SubscriptionCreate
from event_poller_sdk.models.abi import ABIEvent, ABIInput

async def main():
    # Initialize the client
    async with EventStreamer(
        service_url="http://localhost:8000",
        subscriber_id="my-app"
    ) as client:

        # Set up HTTP webhook handler
        handler = client.setup_http_handler(port=8080)

        @handler.on_event("Transfer")
        async def handle_transfers(events):
            for event in events:
                print(f"Transfer: {event['from']} -> {event['to']}: {event['value']}")

        # Start the webhook server
        await handler.start()

        # Create a subscription
        subscription = SubscriptionCreate(
            topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            event_signature=ABIEvent(
                type="event",
                name="Transfer",
                inputs=[
                    ABIInput(name="from", type="address", indexed=True),
                    ABIInput(name="to", type="address", indexed=True),
                    ABIInput(name="value", type="uint256", indexed=False)
                ]
            ),
            addresses=["0xA0b86a33E6417b3c4555ba476F04245600306D5D"],
            start_block=19000000,
            end_block=19010000,
            chain_id=1,
            response_url=handler.get_webhook_url(),
            subscriber_id="my-app"
        )

        result = await client.create_subscription(subscription)
        print(f"Created subscription: {result.id}")

        # Keep running to receive events
        await handler.start_and_wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### WebSocket Example

```python
import asyncio
from event_poller_sdk import EventStreamer
from event_poller_sdk.models.subscriptions import SubscriptionCreate
from event_poller_sdk.models.abi import ABIEvent, ABIInput

async def main():
    async with EventStreamer(
        service_url="http://localhost:8000",
        subscriber_id="my-app"
    ) as client:

        # Set up WebSocket server
        ws_handler = client.setup_websocket_handler(port=8081)

        @ws_handler.on_event("Transfer")
        async def handle_transfers(events):
            for event in events:
                print(f"Transfer: {event['from']} -> {event['to']}: {event['value']}")

        # Start WebSocket server
        await ws_handler.start()

        # Create subscription with WebSocket URL
        subscription = SubscriptionCreate(
            topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            event_signature=ABIEvent(
                type="event",
                name="Transfer",
                inputs=[
                    ABIInput(name="from", type="address", indexed=True),
                    ABIInput(name="to", type="address", indexed=True),
                    ABIInput(name="value", type="uint256", indexed=False)
                ]
            ),
            addresses=["0xA0b86a33E6417b3c4555ba476F04245600306D5D"],
            start_block=19000000,
            chain_id=1,
            response_url=ws_handler.get_websocket_url(),
            subscriber_id="my-app"
        )

        result = await client.create_subscription(subscription)
        print(f"Created subscription: {result.id}")

        # Keep running to receive events
        await ws_handler.start_and_wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### EventStreamer

The main client class for interacting with the Event Streamer service.

```python
class EventStreamer:
    def __init__(
        self,
        service_url: str,
        subscriber_id: str,
        timeout: int = 30,
        api_key: Optional[str] = None,  # Future use
        auth_token: Optional[str] = None,  # Future use
    )
```

#### Subscription Management

```python
# Create a subscription
async def create_subscription(self, subscription: SubscriptionCreate) -> SubscriptionResponse

# List subscriptions
async def list_subscriptions(self, page: int = 1, page_size: int = 20) -> SubscriptionListResponse

# Get a specific subscription
async def get_subscription(self, subscription_id: int) -> SubscriptionResponse

# Update a subscription
async def update_subscription(self, subscription_id: int, update: SubscriptionUpdate) -> SubscriptionResponse

# Delete a subscription
async def delete_subscription(self, subscription_id: int) -> bool

# Confirm event delivery
async def confirm_delivery(self, subscription_id: int, response_id: str) -> bool
```

#### Event Handler Setup

```python
# Set up HTTP webhook handler
def setup_http_handler(
    self,
    port: int = 8080,
    host: str = "0.0.0.0",
    auto_confirm: bool = True
) -> HttpEventHandler

# Set up WebSocket server
def setup_websocket_handler(
    self,
    port: int = 8081,
    host: str = "0.0.0.0",
    auto_confirm: bool = True
) -> WebSocketEventHandler
```

### Event Handlers

Both HTTP and WebSocket handlers support the same event registration patterns:

```python
# Handle specific event types
@handler.on_event("Transfer")
async def handle_transfers(events: List[Dict[str, Any]]):
    for event in events:
        # Process event
        pass

# Handle all events
@handler.on_all_events
async def handle_all_events(events: Dict[str, List[Dict[str, Any]]]):
    for event_name, event_list in events.items():
        # Process events by type
        pass
```

### Models

#### SubscriptionCreate

```python
class SubscriptionCreate(BaseModel):
    topic0: str                    # Event signature hash
    event_signature: ABIEvent      # ABI event definition
    addresses: List[str] = []      # Contract addresses (empty = all)
    start_block: int               # Starting block number
    end_block: Optional[int] = None # Ending block (None = live)
    chain_id: int                  # Blockchain network ID
    response_url: str              # Webhook/WebSocket URL
    subscriber_id: str             # Your service identifier
```

#### ABIEvent

```python
class ABIEvent(BaseModel):
    type: Literal["event"]
    name: str                      # Event name
    inputs: List[ABIInput] = []    # Event parameters
    anonymous: bool = False
```

#### ABIInput

```python
class ABIInput(BaseModel):
    name: Optional[str] = None     # Parameter name
    type: str                      # Solidity type (e.g., "address", "uint256")
    indexed: Optional[bool] = False # Whether parameter is indexed
```

## Event Data Format

Events are delivered in the following format:

```python
{
    "response_id": "550e8400-e29b-41d4-a716-446655440000",
    "subscription_id": 123,  # HTTP only
    "data": {
        "Transfer": [
            {
                # Event-specific fields
                "from": "0x1234567890123456789012345678901234567890",
                "to": "0x0987654321098765432109876543210987654321",
                "value": "1000000000000000000",

                # Metadata fields
                "block_number": 19000001,
                "transaction_hash": "0xabcdef...",
                "log_index": 0,
                "address": "0xA0b86a33E6417b3c4555ba476F04245600306D5D"
            }
        ]
    }
}
```

## Supported Chains

The SDK supports all chains configured in your Event Streamer service:

- **Ethereum Mainnet** (Chain ID: 1)
- **Polygon** (Chain ID: 137)
- **Base** (Chain ID: 8453)
- **Arbitrum One** (Chain ID: 42161)
- **Optimism** (Chain ID: 10)

## Error Handling

The SDK provides comprehensive error handling:

```python
from event_poller_sdk.exceptions import (
    EventPollerSDKError,           # Base exception
    EventPollerConnectionError,    # Connection issues
    EventPollerTimeoutError,       # Request timeouts
    EventPollerValidationError,    # Validation errors
    EventPollerSubscriptionError,  # Subscription errors
)

try:
    subscription = await client.create_subscription(subscription_data)
except EventPollerValidationError as e:
    print(f"Invalid subscription data: {e}")
except EventPollerConnectionError as e:
    print(f"Connection failed: {e}")
```

## Best Practices

### 1. Use Context Managers

Always use the EventStreamer as an async context manager to ensure proper cleanup:

```python
async with EventStreamer(service_url, subscriber_id) as client:
    # Your code here
    pass
```

### 2. Handle Events Efficiently

Process events quickly in your handlers to avoid blocking:

```python
@handler.on_event("Transfer")
async def handle_transfers(events):
    # Process quickly
    for event in events:
        await process_event_async(event)
```

### 3. Use Specific Event Handlers

Register handlers for specific event types rather than using only the global handler:

```python
@handler.on_event("Transfer")
async def handle_transfers(events):
    # Specific handling for transfers
    pass

@handler.on_event("Approval")
async def handle_approvals(events):
    # Specific handling for approvals
    pass
```

### 4. Monitor Your Endpoints

Ensure your webhook/WebSocket endpoints are healthy and accessible:

```python
# HTTP webhook should return 200 status
# WebSocket should stay connected and respond to messages
```

## Development

### Requirements

- Python 3.11+
- aiohttp
- blacksheep
- websockets
- pydantic
- eth-typing

### Installation for Development

```bash
git clone https://github.com/dcentralab/event-poller-sdk
cd event-poller-sdk
pip install -e ".[dev]"
```

### Running Examples

```bash
# HTTP webhook example
python examples/http_webhook_example.py

# WebSocket example
python examples/websocket_example.py
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
