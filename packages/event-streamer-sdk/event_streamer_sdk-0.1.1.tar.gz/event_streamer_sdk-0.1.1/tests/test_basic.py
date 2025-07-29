"""
Basic tests for Event Streamer SDK structure and imports.
"""


def test_imports():
    """Test that all main SDK components can be imported."""
    # Test main package imports
    from event_poller_sdk import EventStreamer

    # Test handler imports
    from event_poller_sdk.http_handler.server import HttpEventHandler

    # Test model imports
    from event_poller_sdk.websocket_handler.server import WebSocketEventHandler

    # Verify classes exist
    assert EventStreamer is not None
    assert HttpEventHandler is not None
    assert WebSocketEventHandler is not None


def test_abi_models():
    """Test ABI model creation and validation."""
    from event_poller_sdk.models.abi import ABIEvent, ABIInput

    # Test ABIInput creation
    input_param = ABIInput(name="from", type="address", indexed=True)
    assert input_param.name == "from"
    assert input_param.type == "address"
    assert input_param.indexed is True

    # Test ABIEvent creation
    event = ABIEvent(
        type="event",
        name="Transfer",
        inputs=[
            ABIInput(name="from", type="address", indexed=True),
            ABIInput(name="to", type="address", indexed=True),
            ABIInput(name="value", type="uint256", indexed=False),
        ],
    )
    assert event.type == "event"
    assert event.name == "Transfer"
    assert len(event.inputs) == 3


def test_subscription_models():
    """Test subscription model creation and validation."""
    from event_poller_sdk.models.abi import ABIEvent, ABIInput
    from event_poller_sdk.models.subscriptions import SubscriptionCreate

    # Create a subscription
    subscription = SubscriptionCreate(
        topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        event_signature=ABIEvent(
            type="event",
            name="Transfer",
            inputs=[
                ABIInput(name="from", type="address", indexed=True),
                ABIInput(name="to", type="address", indexed=True),
                ABIInput(name="value", type="uint256", indexed=False),
            ],
        ),
        addresses=["0xA0b86a33E6417b3c4555ba476F04245600306D5D"],
        start_block=19000000,
        end_block=19010000,
        chain_id=1,
        response_url="https://api.example.com/webhook",
        subscriber_id="test-app",
    )

    assert subscription.topic0.startswith("0x")
    assert len(subscription.topic0) == 66
    assert subscription.chain_id == 1
    assert subscription.start_block == 19000000
    assert subscription.end_block == 19010000


def test_event_streamer_initialization():
    """Test EventStreamer initialization."""
    from event_poller_sdk import EventStreamer

    client = EventStreamer(service_url="http://localhost:8000", subscriber_id="test-app")

    assert client.service_url == "http://localhost:8000"
    assert client.subscriber_id == "test-app"
    assert client.timeout == 30.0  # default
    assert client.session is None  # not initialized yet


def test_event_handlers_creation():
    """Test that event handlers can be created."""
    from event_poller_sdk import EventStreamer

    client = EventStreamer(service_url="http://localhost:8000", subscriber_id="test-app")

    # Test HTTP handler creation
    http_handler = client.setup_http_handler(port=8080)
    assert http_handler.port == 8080
    assert http_handler.auto_confirm is True

    # Test WebSocket handler creation
    ws_handler = client.setup_websocket_handler(port=8081)
    assert ws_handler.port == 8081
    assert ws_handler.auto_confirm is True


def test_exceptions():
    """Test custom exceptions."""
    from event_poller_sdk.exceptions import (
        EventStreamerAuthError,
        EventStreamerConnectionError,
        EventStreamerSDKError,
        EventStreamerSubscriptionError,
        EventStreamerTimeoutError,
        EventStreamerValidationError,
    )

    # Test exception hierarchy
    assert issubclass(EventStreamerConnectionError, EventStreamerSDKError)
    assert issubclass(EventStreamerAuthError, EventStreamerSDKError)
    assert issubclass(EventStreamerTimeoutError, EventStreamerSDKError)
    assert issubclass(EventStreamerValidationError, EventStreamerSDKError)
    assert issubclass(EventStreamerSubscriptionError, EventStreamerSDKError)

    # Test exception creation
    error = EventStreamerConnectionError("Connection failed")
    assert str(error) == "Connection failed"
    assert isinstance(error, EventStreamerSDKError)
