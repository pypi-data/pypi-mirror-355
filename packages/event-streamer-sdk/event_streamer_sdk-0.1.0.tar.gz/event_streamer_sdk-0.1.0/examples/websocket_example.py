"""
Example: Using Event Streamer SDK with WebSocket

This example demonstrates how to:
1. Set up a WebSocket server
2. Create a subscription for live events
3. Process incoming events in real-time
4. Handle automatic event confirmation
"""

import asyncio

from event_poller_sdk import EventStreamer
from event_poller_sdk.models.abi import ABIEvent, ABIInput
from event_poller_sdk.models.subscriptions import SubscriptionCreate


async def main():
    """Main example function."""

    # Initialize the EventStreamer client
    async with EventStreamer(
        service_url="http://localhost:8000", subscriber_id="websocket-example"
    ) as client:
        # Set up WebSocket server
        ws_handler = client.setup_websocket_handler(port=8081, host="0.0.0.0")

        # Register event handlers
        @ws_handler.on_event("Transfer")
        async def handle_transfer_events(events):
            """Handle Transfer events."""
            print(f"🔄 Received {len(events)} Transfer events:")
            for event in events:
                from_addr = event["from"][:6] + "..." + event["from"][-4:]
                to_addr = event["to"][:6] + "..." + event["to"][-4:]
                print(f"  💰 {from_addr} → {to_addr}: {event['value']} tokens")
                print(f"    📦 Block: {event['block_number']}")

        @ws_handler.on_event("Approval")
        async def handle_approval_events(events):
            """Handle Approval events."""
            print(f"✅ Received {len(events)} Approval events:")
            for event in events:
                owner = event["owner"][:6] + "..." + event["owner"][-4:]
                spender = event["spender"][:6] + "..." + event["spender"][-4:]
                print(f"  🔑 {owner} approved {spender}: {event['value']} tokens")

        # Global handler for comprehensive event logging
        @ws_handler.on_all_events
        async def handle_all_events(events):
            """Log all events for monitoring."""
            total_events = sum(len(event_list) for event_list in events.values())
            if total_events > 0:
                print(f"📊 Total events received: {total_events}")
                for event_name, event_list in events.items():
                    print(f"  - {event_name}: {len(event_list)} events")

        # Start the WebSocket server
        print("🚀 Starting WebSocket server...")
        await ws_handler.start()

        # Create a subscription for live Transfer events
        print("📝 Creating subscription for live Transfer events...")
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
            addresses=["0xA0b86a33E6417b3c4555ba476F04245600306D5D"],  # Specific token
            start_block=19000000,
            # No end_block = live monitoring
            chain_id=1,  # Ethereum mainnet
            response_url=ws_handler.get_websocket_url(),
            subscriber_id="websocket-example",
        )

        result = await client.create_subscription(subscription)
        print(f"✅ Created subscription with ID: {result.id}")
        print(f"🔗 WebSocket URL: {ws_handler.get_websocket_url()}")
        print(f"⛓️  Monitoring chain: {subscription.chain_id}")
        print(
            f"📍 Contract: "
            f"{subscription.addresses[0] if subscription.addresses else 'All contracts'}"
        )

        # Keep the server running to receive events
        print("\n🎧 WebSocket server is listening for events...")
        print("   Press Ctrl+C to stop...")
        try:
            await ws_handler.start_and_wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping WebSocket server...")
        finally:
            await ws_handler.stop()
            print("✋ WebSocket server stopped")


if __name__ == "__main__":
    asyncio.run(main())
