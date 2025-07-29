"""
HTTP webhook handler for Event Streamer SDK using BlackSheep.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import uvicorn
from blacksheep import Application, Request
from blacksheep import json as response_json

from ..models.events import EventDeliveryPayload

if TYPE_CHECKING:
    from ..client import EventStreamer


class HttpEventHandler:
    """HTTP webhook handler using BlackSheep."""

    def __init__(
        self,
        event_streamer: "EventStreamer",
        port: int = 8080,
        host: str = "0.0.0.0",
        auto_confirm: bool = True,
    ) -> None:
        self.event_streamer = event_streamer
        self.port = port
        self.host = host
        self.auto_confirm = auto_confirm

        # Event handlers storage
        self._event_handlers: dict[str, Callable[[list[dict[str, Any]]], Awaitable[None]]] = {}
        self._global_handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None

        # BlackSheep app
        self.app = Application()
        self._setup_routes()

        # Server management
        self._server_task: asyncio.Task[None] | None = None

    def _setup_routes(self) -> None:
        """Set up BlackSheep routes."""

        @self.app.router.post("/webhook")
        async def handle_webhook(request: Request) -> Any:
            """Handle incoming webhook events."""
            try:
                raw_data = await request.json()

                # Validate the payload
                try:
                    delivery_payload = EventDeliveryPayload(**raw_data)
                except Exception as e:
                    return response_json({"error": f"Invalid payload: {str(e)}"}, 400)

                # Process the webhook
                await self._process_webhook(delivery_payload)

                return response_json({"status": "ok"}, 200)

            except Exception as e:
                return response_json({"error": str(e)}, 500)

    async def _process_webhook(self, payload: EventDeliveryPayload) -> None:
        """Process incoming webhook data."""
        response_id = payload.response_id
        subscription_id = payload.subscription_id
        events_data = payload.data

        try:
            # Process each event type
            for event_name, event_list in events_data.items():
                if event_name in self._event_handlers:
                    await self._event_handlers[event_name](event_list)
                elif self._global_handler:
                    await self._global_handler({event_name: event_list})

            # Auto-confirm if enabled and we have the necessary info
            if self.auto_confirm and response_id and subscription_id:
                await self._confirm_delivery(subscription_id, response_id)

        except Exception as e:
            print(f"Error processing webhook events: {e}")

    async def _confirm_delivery(self, subscription_id: int, response_id: str) -> None:
        """Confirm event delivery."""
        try:
            await self.event_streamer.confirm_delivery(subscription_id, response_id)
        except Exception as e:
            print(f"Failed to confirm delivery: {e}")

    def on_event(
        self, event_name: str
    ) -> Callable[
        [Callable[[list[dict[str, Any]]], Awaitable[None]]],
        Callable[[list[dict[str, Any]]], Awaitable[None]],
    ]:
        """Decorator to register event handler for specific event type."""

        def decorator(
            func: Callable[[list[dict[str, Any]]], Awaitable[None]],
        ) -> Callable[[list[dict[str, Any]]], Awaitable[None]]:
            self._event_handlers[event_name] = func
            return func

        return decorator

    def on_all_events(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """Register global event handler that receives all events."""
        self._global_handler = handler

    def get_webhook_url(self) -> str:
        """Get the webhook URL for subscription configuration."""
        return f"http://{self.host}:{self.port}/webhook"

    async def start(self) -> None:
        """Start the HTTP webhook server."""

        async def run_server() -> None:
            """Run the uvicorn server."""
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=False,
            )
            server = uvicorn.Server(config)
            await server.serve()

        self._server_task = asyncio.create_task(run_server())
        print(f"HTTP webhook handler started on {self.host}:{self.port}")

        # Wait a bit for the server to start
        await asyncio.sleep(0.1)

    async def start_and_wait(self) -> None:
        """Start the server and wait for it to finish."""
        await self.start()

        if self._server_task:
            await self._server_task

    async def stop(self) -> None:
        """Stop the HTTP webhook server."""
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        print("HTTP webhook handler stopped")
