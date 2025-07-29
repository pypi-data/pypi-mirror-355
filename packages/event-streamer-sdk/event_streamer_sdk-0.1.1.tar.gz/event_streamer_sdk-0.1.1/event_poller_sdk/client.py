"""
Main EventStreamer client for interacting with Event Streamer service.
"""

from typing import Any

import aiohttp

from .exceptions import (
    EventStreamerConnectionError,
    EventStreamerSubscriptionError,
    EventStreamerTimeoutError,
    EventStreamerValidationError,
)
from .http_handler.server import HttpEventHandler
from .models.subscriptions import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate
from .websocket_handler.server import WebSocketEventHandler


class EventStreamer:
    """Main SDK client for interacting with Event Streamer service."""

    def __init__(
        self,
        service_url: str,
        subscriber_id: str,
        *,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize the EventStreamer client.

        Args:
            service_url: Base URL of the Event Streamer service
            subscriber_id: Unique identifier for this subscriber
            timeout: Request timeout in seconds
            headers: Optional additional headers for requests
        """
        self.service_url = service_url.rstrip("/")
        self.subscriber_id = subscriber_id
        self.timeout = timeout
        self.headers = headers or {}
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "EventStreamer":
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure the HTTP session is initialized."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.headers,
            )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Event Streamer service."""
        await self._ensure_session()

        if not self.session:
            raise EventStreamerConnectionError("HTTP session not initialized")

        url = f"{self.service_url}{endpoint}"

        try:
            async with self.session.request(method, url, json=json, params=params) as response:
                response_text = await response.text()

                if response.status >= 500:
                    error_text = response_text or f"HTTP {response.status}"
                    raise EventStreamerConnectionError(f"Service error: {error_text}")
                elif response.status >= 400:
                    error_text = response_text or f"HTTP {response.status}"
                    raise EventStreamerValidationError(f"Request error: {error_text}")

                return await response.json()  # type: ignore[no-any-return]

        except TimeoutError:
            raise EventStreamerTimeoutError(f"Request to {url} timed out")
        except aiohttp.ClientError as e:
            raise EventStreamerConnectionError(f"Connection error: {str(e)}")

    async def create_subscription(self, subscription: SubscriptionCreate) -> SubscriptionResponse:
        """
        Create a new subscription.

        Args:
            subscription: The subscription configuration

        Returns:
            The created subscription with assigned ID

        Raises:
            EventStreamerSubscriptionError: If subscription creation fails
        """
        subscription_data = subscription.model_dump()
        subscription_data["subscriber_id"] = self.subscriber_id

        try:
            response = await self._request("POST", "/subscriptions", json=subscription_data)
            return SubscriptionResponse(**response)
        except (
            EventStreamerConnectionError,
            EventStreamerTimeoutError,
            EventStreamerValidationError,
        ) as e:
            # Re-raise as subscription error with more context
            raise EventStreamerSubscriptionError(f"Failed to create subscription: {str(e)}")

    async def get_subscription(self, subscription_id: int) -> SubscriptionResponse:
        """
        Get a subscription by ID.

        Args:
            subscription_id: ID of the subscription to retrieve

        Returns:
            The subscription data

        Raises:
            EventStreamerSubscriptionError: If subscription not found
        """
        try:
            response = await self._request(
                "GET",
                f"/subscriptions/{subscription_id}",
                params={"subscriber_id": self.subscriber_id},
            )
            return SubscriptionResponse(**response)
        except EventStreamerValidationError as e:
            if "404" in str(e):
                raise EventStreamerSubscriptionError(f"Subscription {subscription_id} not found")
            raise

    async def update_subscription(
        self, subscription_id: int, updates: SubscriptionUpdate
    ) -> SubscriptionResponse:
        """
        Update a subscription.

        Args:
            subscription_id: ID of the subscription to update
            updates: The subscription updates

        Returns:
            The updated subscription

        Raises:
            EventStreamerSubscriptionError: If update fails
        """
        update_data = updates.model_dump(exclude_unset=True)
        try:
            response = await self._request(
                "PUT", f"/subscriptions/{subscription_id}", json=update_data
            )
            return SubscriptionResponse(**response)
        except EventStreamerValidationError as e:
            if "404" in str(e):
                raise EventStreamerSubscriptionError(f"Subscription {subscription_id} not found")
            raise EventStreamerSubscriptionError(f"Failed to update subscription: {str(e)}")

    async def delete_subscription(self, subscription_id: int) -> None:
        """
        Delete a subscription.

        Args:
            subscription_id: ID of the subscription to delete

        Raises:
            EventStreamerSubscriptionError: If deletion fails
        """
        try:
            await self._request("DELETE", f"/subscriptions/{subscription_id}")
        except EventStreamerValidationError as e:
            if "404" in str(e):
                raise EventStreamerSubscriptionError(f"Subscription {subscription_id} not found")
            raise EventStreamerSubscriptionError(f"Failed to delete subscription: {str(e)}")

    async def confirm_delivery(self, subscription_id: int, response_id: str) -> None:
        """
        Confirm successful delivery of events.

        Args:
            subscription_id: ID of the subscription
            response_id: ID of the response to confirm
        """
        await self._request(
            "POST",
            "/confirmations",
            json={
                "subscription_id": subscription_id,
                "response_id": response_id,
            },
        )

    def setup_http_handler(
        self,
        *,
        port: int = 8080,
        host: str = "localhost",
        auto_confirm: bool = True,
    ) -> HttpEventHandler:
        """
        Set up an HTTP webhook handler.

        Args:
            port: Port to listen on
            host: Host to bind to
            auto_confirm: Whether to automatically confirm delivery

        Returns:
            Configured HTTP event handler
        """
        return HttpEventHandler(
            event_streamer=self, port=port, host=host, auto_confirm=auto_confirm
        )

    def setup_websocket_handler(
        self,
        *,
        port: int = 8081,
        host: str = "localhost",
        auto_confirm: bool = True,
    ) -> WebSocketEventHandler:
        """
        Set up a WebSocket event handler.

        Args:
            port: Port to listen on
            host: Host to bind to
            auto_confirm: Whether to automatically confirm delivery

        Returns:
            Configured WebSocket event handler
        """
        return WebSocketEventHandler(
            event_streamer=self, port=port, host=host, auto_confirm=auto_confirm
        )
