"""
Event data models for Event Streamer SDK.

NOTE: There is some conceptual overlap with src/schemas/events.py (BaseEvent) in the main project,
but these models are optimized for SDK usage and event delivery payloads.
TODO: Consider making the main project schemas available as a dependency for better type
consistency.

These models handle event delivery payloads and event data structures.
"""

from typing import Any

from pydantic import BaseModel, Field


class EventData(BaseModel):
    """Schema for individual event data in delivery payloads."""

    # Event-specific decoded data (dynamic fields)
    # This will contain the actual event parameters like 'from', 'to', 'value' for Transfer events

    # Metadata fields that are always present in delivered events
    block_number: int = Field(
        description="Block number where the event occurred", examples=[19000001]
    )
    transaction_hash: str = Field(
        description="Transaction hash", examples=["0xabcdef1234567890abcdef1234567890abcdef12"]
    )
    log_index: int = Field(description="Log index within the transaction", examples=[0])
    address: str = Field(
        description="Contract address that emitted the event",
        examples=["0xA0b86a33E6417b3c4555ba476F04245600306D5D"],
    )
    timestamp: str | None = Field(
        description="Block timestamp in ISO format",
        examples=["2024-05-23T10:30:00.000Z"],
        default=None,
    )

    class Config:
        extra = "allow"  # Allow additional fields for event-specific data


# SDK-specific delivery payload models (these don't exist upstream)
class EventDeliveryPayload(BaseModel):
    """Schema for event delivery payload from Event Streamer service."""

    response_id: str = Field(
        description="Unique response ID for delivery confirmation",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    subscription_id: int | None = Field(
        description="Subscription ID (may be included in HTTP webhooks)",
        examples=[123],
        default=None,
    )
    data: dict[str, list[dict[str, Any]]] = Field(
        description="Event data grouped by event name",
        examples=[
            {
                "Transfer": [
                    {
                        "from": "0x1234567890123456789012345678901234567890",
                        "to": "0x0987654321098765432109876543210987654321",
                        "value": "1000000000000000000",
                        "block_number": 19000001,
                        "transaction_hash": "0xabcdef...",
                        "log_index": 0,
                        "address": "0xA0b86a33E6417b3c4555ba476F04245600306D5D",
                    }
                ]
            }
        ],
    )


class WebSocketDeliveryPayload(BaseModel):
    """Schema for WebSocket event delivery payload."""

    route: str = Field(description="WebSocket route identifier", examples=["subscription-123"])
    response_id: str = Field(
        description="Unique response ID for delivery confirmation",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    data: dict[str, list[dict[str, Any]]] = Field(
        description="Event data grouped by event name",
        examples=[
            {
                "Transfer": [
                    {
                        "from": "0x1234567890123456789012345678901234567890",
                        "to": "0x0987654321098765432109876543210987654321",
                        "value": "1000000000000000000",
                        "block_number": 19000001,
                        "transaction_hash": "0xabcdef...",
                        "log_index": 0,
                        "address": "0xA0b86a33E6417b3c4555ba476F04245600306D5D",
                    }
                ]
            }
        ],
    )
