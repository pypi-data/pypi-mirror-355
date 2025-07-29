"""
Example: Using Event Streamer SDK with HTTP Webhooks

This example demonstrates how to:
1. Set up an HTTP webhook handler
2. Create a subscription for Transfer events
3. Process incoming events
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
        service_url="http://localhost:8000", subscriber_id="example-app"
    ) as client:
        # Set up HTTP webhook handler
        handler = client.setup_http_handler(port=8080, host="0.0.0.0")

        # Register event handlers
        @handler.on_event("Transfer")
        async def handle_transfer_events(events):
            """Handle Transfer events."""
            print(f"Received {len(events)} Transfer events:")
            for event in events:
                print(f"  Transfer: {event['from']} -> {event['to']}: {event['value']} tokens")
                print(f"    Block: {event['block_number']}, Tx: {event['transaction_hash']}")

        @handler.on_event("Approval")
        async def handle_approval_events(events):
            """Handle Approval events."""
            print(f"Received {len(events)} Approval events:")
            for event in events:
                print(
                    f"Approval: {event['owner']} approved {event['spender']}: "
                    f"{event['value']} tokens"
                )

        # Global handler for any other events
        @handler.on_all_events
        async def handle_all_events(events):
            """Handle any events not specifically registered."""
            for event_name, event_list in events.items():
                if event_name not in ["Transfer", "Approval"]:
                    print(f"Received {len(event_list)} {event_name} events")

        # Start the webhook server
        print("Starting HTTP webhook server...")
        await handler.start()

        # Create a subscription for Transfer events
        print("Creating subscription for Transfer events...")
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
            addresses=[],  # Monitor all contracts
            start_block=19000000,
            end_block=19001000,  # Historical range
            chain_id=1,  # Ethereum mainnet
            response_url=handler.get_webhook_url(),
            subscriber_id="example-app",
        )

        result = await client.create_subscription(subscription)
        print(f"Created subscription with ID: {result.id}")
        print(f"Webhook URL: {handler.get_webhook_url()}")

        # Keep the server running to receive events
        print("Webhook server is running. Press Ctrl+C to stop...")
        try:
            await handler.start_and_wait()
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            await handler.stop()


if __name__ == "__main__":
    asyncio.run(main())
