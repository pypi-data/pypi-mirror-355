"""
WebSocket event handler for Event Streamer SDK.

This creates a WebSocket server to receive events from the Event Streamer service.
"""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import websockets
from pydantic import ValidationError

from ..models.events import WebSocketDeliveryPayload

if TYPE_CHECKING:
    from ..client import EventStreamer


class WebSocketEventHandler:
    """WebSocket event handler - runs a WebSocket server to receive events."""

    def __init__(
        self,
        event_streamer: "EventStreamer",
        port: int = 8081,
        host: str = "0.0.0.0",
        auto_confirm: bool = True,
    ) -> None:
        """
        Initialize the WebSocket event handler.

        Args:
            event_streamer: The EventStreamer client instance
            port: Port to run the WebSocket server on
            host: Host to bind the server to
            auto_confirm: Whether to automatically confirm event deliveries
        """
        self.event_streamer = event_streamer
        self.port = port
        self.host = host
        self.auto_confirm = auto_confirm

        # Event handlers
        self._event_handlers: dict[str, Callable[[list[dict[str, Any]]], Awaitable[None]]] = {}
        self._global_handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None

        # Server management
        self._server: Any = None
        self._server_task: asyncio.Task[None] | None = None
        self._running = False

        # Logger
        self.logger = logging.getLogger(__name__)

    async def _websocket_handler(self, websocket: websockets.ServerConnection) -> None:
        """Handle incoming WebSocket connections."""
        self.logger.info(f"Event Streamer service connected: {websocket.remote_address}")

        try:
            async for message in websocket:
                try:
                    self.logger.debug(f"Received message: {message!r}")
                    payload = json.loads(message)

                    # Process the event message
                    await self._process_message(websocket, payload)

                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error: {e}")
                    await websocket.send(json.dumps({"error": f"Invalid JSON: {str(e)}"}))
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({"error": str(e)}))

        except websockets.exceptions.ConnectionClosed:
            self.logger.info("Event Streamer service disconnected")
        except Exception as e:
            self.logger.error(f"Unexpected error in websocket handler: {e}")
        finally:
            self.logger.info("Connection handler exiting")

    async def _process_message(
        self, websocket: websockets.ServerConnection, payload: dict[str, Any]
    ) -> None:
        """Process incoming WebSocket message."""

        try:
            # Validate the payload
            if "response_id" in payload and "data" in payload:
                # This looks like a direct event delivery
                delivery_payload = WebSocketDeliveryPayload(**payload)
                await self._process_event_data(delivery_payload)

                # Send acknowledgment
                await websocket.send(
                    json.dumps({"status": "received", "response_id": delivery_payload.response_id})
                )

            else:
                # Unknown message format
                await websocket.send(
                    json.dumps(
                        {"error": "Unknown message format. Expected WebSocket delivery payload."}
                    )
                )

        except ValidationError as e:
            self.logger.warning(f"Validation error: {e.errors()}")
            await websocket.send(json.dumps({"error": e.errors()}))
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            await websocket.send(json.dumps({"error": str(e)}))

    async def _process_event_data(self, payload: WebSocketDeliveryPayload) -> None:
        """Process event data from WebSocket message."""

        try:
            # Process each event type
            for event_name, event_list in payload.data.items():
                if event_name in self._event_handlers:
                    await self._event_handlers[event_name](event_list)
                elif self._global_handler:
                    await self._global_handler({event_name: event_list})

            # Auto-confirm if enabled
            if self.auto_confirm and payload.response_id:
                # Extract subscription_id from route if available
                subscription_id = None
                if payload.route and payload.route.startswith("subscription-"):
                    try:
                        subscription_id = int(payload.route.split("-")[1])
                    except (IndexError, ValueError):
                        pass

                if subscription_id:
                    await self._confirm_delivery(subscription_id, payload.response_id)

        except Exception as e:
            self.logger.error(f"Error processing event data: {e}")

    async def _confirm_delivery(self, subscription_id: int, response_id: str) -> None:
        """Confirm event delivery via HTTP API."""
        try:
            await self.event_streamer.confirm_delivery(subscription_id, response_id)
        except Exception as e:
            self.logger.error(f"Failed to confirm delivery: {e}")

    def on_event(
        self, event_name: str
    ) -> Callable[
        [Callable[[list[dict[str, Any]]], Awaitable[None]]],
        Callable[[list[dict[str, Any]]], Awaitable[None]],
    ]:
        """
        Decorator to register event handler for specific event type.

        Args:
            event_name: Name of the event to handle (e.g., "Transfer")

        Returns:
            Decorator function

        Example:
            @handler.on_event("Transfer")
            async def handle_transfers(events):
                for event in events:
                    print(f"Transfer: {event}")
        """

        def decorator(
            func: Callable[[list[dict[str, Any]]], Awaitable[None]],
        ) -> Callable[[list[dict[str, Any]]], Awaitable[None]]:
            self._event_handlers[event_name] = func
            return func

        return decorator

    def on_all_events(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """
        Register global event handler that receives all events.

        Args:
            handler: Function to handle all events

        Example:
            @handler.on_all_events
            async def handle_all_events(events):
                for event_name, event_list in events.items():
                    print(f"Event {event_name}: {event_list}")
        """
        self._global_handler = handler

    def get_websocket_url(self) -> str:
        """
        Get the WebSocket server URL for subscription configuration.

        Returns:
            WebSocket URL that can be used in subscription response_url
        """
        return f"ws://{self.host}:{self.port}"

    async def start(self) -> None:
        """Start the WebSocket server."""

        async def run_server() -> None:
            """Run the WebSocket server."""
            self.logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
            try:
                self._server = await websockets.serve(self._websocket_handler, self.host, self.port)
                self.logger.info("WebSocket server started successfully")
                self._running = True

                try:
                    # Run forever until cancelled
                    await asyncio.Future()
                except asyncio.CancelledError:
                    self.logger.info("WebSocket server received cancellation request")
                    # Close the server when cancelled
                    if self._server:
                        self._server.close()
                        await self._server.wait_closed()
                    self.logger.info("WebSocket server closed after cancellation")
                    raise

            except Exception as e:
                self.logger.error(f"WebSocket server error: {e}")
                raise
            finally:
                self._running = False
                self.logger.info("WebSocket server exiting")

        self._server_task = asyncio.create_task(run_server())
        print(f"WebSocket event handler started on {self.host}:{self.port}")

        # Wait a bit for the server to start
        await asyncio.sleep(0.1)

    async def start_and_wait(self) -> None:
        """Start the server and wait for it to finish."""
        await self.start()

        if self._server_task:
            await self._server_task

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        self._running = False

        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass

        print("WebSocket event handler stopped")
