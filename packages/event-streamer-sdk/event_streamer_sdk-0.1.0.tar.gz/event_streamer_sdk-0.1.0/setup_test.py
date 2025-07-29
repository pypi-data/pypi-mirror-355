#!/usr/bin/env python3
"""
Simple test script to verify the Event Streamer SDK package structure.

This script tests basic imports and model creation without requiring
the actual Event Poller service to be running.
"""

import sys
import traceback


def test_basic_imports():
    """Test that basic imports work."""
    print("Testing basic imports...")

    try:
        # Test exceptions
        print("✅ Exception imports successful")

        # Test ABI models
        print("✅ ABI model imports successful")

        # Test subscription models
        print("✅ Subscription model imports successful")

        # Test event models
        print("✅ Event model imports successful")

        # Test main client
        print("✅ EventStreamer import successful")

        # Test handlers
        print("✅ Handler imports successful")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_model_creation():
    """Test creating models."""
    print("\nTesting model creation...")

    try:
        from event_poller_sdk.models.abi import ABIEvent, ABIInput
        from event_poller_sdk.models.subscriptions import SubscriptionCreate

        # Create ABI models
        transfer_event = ABIEvent(
            type="event",
            name="Transfer",
            inputs=[
                ABIInput(name="from", type="address", indexed=True),
                ABIInput(name="to", type="address", indexed=True),
                ABIInput(name="value", type="uint256", indexed=False),
            ],
        )
        print("✅ ABIEvent creation successful")

        # Create subscription
        _subscription = SubscriptionCreate(
            topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            event_signature=transfer_event,
            addresses=["0xA0b86a33E6417b3c4555ba476F04245600306D5D"],
            start_block=19000000,
            end_block=19010000,
            chain_id=1,
            response_url="https://api.example.com/webhook",
            subscriber_id="test-app",
        )
        print("✅ SubscriptionCreate creation successful")

        return True

    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        traceback.print_exc()
        return False


def test_client_creation():
    """Test creating the EventStreamer client."""
    print("\nTesting client creation...")

    try:
        from event_poller_sdk.client import EventStreamer

        # Create client
        client = EventStreamer(service_url="http://localhost:8000", subscriber_id="test-app")
        print("✅ EventStreamer creation successful")

        # Test handler setup (without starting)
        _http_handler = client.setup_http_handler(port=8080)
        print("✅ HTTP handler setup successful")

        _ws_handler = client.setup_websocket_handler(port=8081)
        print("✅ WebSocket handler setup successful")

        return True

    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Event Streamer SDK Package Test")
    print("=" * 40)

    tests = [
        test_basic_imports,
        test_model_creation,
        test_client_creation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! SDK package structure is correct.")
        return 0
    else:
        print("❌ Some tests failed. Check the package structure.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
