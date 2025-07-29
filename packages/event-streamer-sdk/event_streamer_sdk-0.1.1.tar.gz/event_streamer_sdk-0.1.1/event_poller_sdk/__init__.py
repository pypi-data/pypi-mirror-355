"""
Event Streamer SDK

A Python SDK for interacting with the Event Streamer blockchain event monitoring service.
"""

from .client import EventStreamer
from .exceptions import EventStreamerAuthError, EventStreamerConnectionError, EventStreamerSDKError

__version__ = "0.1.0"
__all__ = [
    "EventStreamer",
    "EventStreamerSDKError",
    "EventStreamerConnectionError",
    "EventStreamerAuthError",
]
