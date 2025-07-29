"""
Event Poller Schemas - Shared Pydantic models for Event Poller ecosystem.

This package contains all the shared Pydantic schemas used by both the main
Event Poller service and the Event Poller SDK. This ensures consistency
and eliminates duplication across the ecosystem.
"""

from .abi import ABIEvent, ABIInput
from .confirmations import ConfirmationRequest, ConfirmationResponse
from .events import BaseEvent
from .subscriptions import (
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
)

__version__ = "0.1.0"

__all__ = [
    # ABI models
    "ABIEvent",
    "ABIInput",
    # Confirmation models
    "ConfirmationRequest",
    "ConfirmationResponse",
    # Event models
    "BaseEvent",
    # Subscription models
    "SubscriptionCreate",
    "SubscriptionListResponse",
    "SubscriptionResponse",
    "SubscriptionUpdate",
]
