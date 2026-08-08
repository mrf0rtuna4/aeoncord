"""
Discord Gateway WebSocket adapter.
"""

from __future__ import annotations

import asyncio
import json
import zlib
from collections.abc import Awaitable, Callable

import aiohttp

from aeoncord.core.domain.models import DomainEvent
from aeoncord.core.ports import EventHandler, GatewayConnection

from aeoncord.adapters.gateway.mapper import GatewayMapper
from aeoncord.adapters.gateway.parser import GatewayParser


EventCallback = Callable[[DomainEvent], Awaitable[None]]


class Opcode:
    """Discord Gateway opcodes."""

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class GatewayEvent:
    """Discord Gateway dispatch event names."""

    READY = "READY"
    RESUMED = "RESUMED"

    MESSAGE_CREATE = "MESSAGE_CREATE"
    MESSAGE_UPDATE = "MESSAGE_UPDATE"
    MESSAGE_DELETE = "MESSAGE_DELETE"

    MESSAGE_REACTION_ADD = "MESSAGE_REACTION_ADD"
    MESSAGE_REACTION_REMOVE = "MESSAGE_REACTION_REMOVE"
    MESSAGE_REACTION_REMOVE_ALL = "MESSAGE_REACTION_REMOVE_ALL"
    MESSAGE_REACTION_REMOVE_EMOJI = "MESSAGE_REACTION_REMOVE_EMOJI"

    PRESENCE_UPDATE = "PRESENCE_UPDATE"
    TYPING_START = "TYPING_START"
    USER_UPDATE = "USER_UPDATE"

    VOICE_STATE_UPDATE = "VOICE_STATE_UPDATE"
    VOICE_SERVER_UPDATE = "VOICE_SERVER_UPDATE"

    GUILD_CREATE = "GUILD_CREATE"
    GUILD_UPDATE = "GUILD_UPDATE"
    GUILD_DELETE = "GUILD_DELETE"
    GUILD_BAN_ADD = "GUILD_BAN_ADD"
    GUILD_BAN_REMOVE = "GUILD_BAN_REMOVE"
    GUILD_EMOJIS_UPDATE = "GUILD_EMOJIS_UPDATE"
    GUILD_INTEGRATIONS_UPDATE = "GUILD_INTEGRATIONS_UPDATE"

    GUILD_MEMBER_ADD = "GUILD_MEMBER_ADD"
    GUILD_MEMBER_REMOVE = "GUILD_MEMBER_REMOVE"
    GUILD_MEMBER_UPDATE = "GUILD_MEMBER_UPDATE"
    GUILD_MEMBERS_CHUNK = "GUILD_MEMBERS_CHUNK"

    GUILD_ROLE_CREATE = "GUILD_ROLE_CREATE"
    GUILD_ROLE_UPDATE = "GUILD_ROLE_UPDATE"
    GUILD_ROLE_DELETE = "GUILD_ROLE_DELETE"

    CHANNEL_CREATE = "CHANNEL_CREATE"
    CHANNEL_UPDATE = "CHANNEL_UPDATE"
    CHANNEL_DELETE = "CHANNEL_DELETE"
    CHANNEL_PINS_UPDATE = "CHANNEL_PINS_UPDATE"

    WEBHOOKS_UPDATE = "WEBHOOKS_UPDATE"
    INVITE_CREATE = "INVITE_CREATE"
    INVITE_DELETE = "INVITE_DELETE"

    INTERACTION_CREATE = "INTERACTION_CREATE"

    STAGE_INSTANCE_CREATE = "STAGE_INSTANCE_CREATE"
    STAGE_INSTANCE_UPDATE = "STAGE_INSTANCE_UPDATE"
    STAGE_INSTANCE_DELETE = "STAGE_INSTANCE_DELETE"


class DiscordGateway(GatewayConnection, EventHandler):
    """
    Discord Gateway WebSocket connection.

    This class is responsible only for:
    - WebSocket connection;
    - receiving Discord Gateway envelopes;
    - handling Gateway protocol events;
    - passing event payloads through parser and mapper.
    """

    GATEWAY_URL = (
        "wss://gateway.discord.gg/"
        "?v=10&encoding=json&compression=zlib-stream"
    )

    def __init__(self, token: str) -> None:
        self.token = token

        self._session: aiohttp.ClientSession | None = None
        self.ws: aiohttp.ClientWebSocketResponse | None = None

        self._connected = False
        self._should_reconnect = True

        self._session_id: str | None = None
        self._sequence: int | None = None
        self._heartbeat_interval: int = 0

        self._heartbeat_task: asyncio.Task[None] | None = None
        self._receive_task: asyncio.Task[None] | None = None

        self._event_handlers: dict[str, list[EventCallback]] = {}

        self._decompress_buffer = zlib.decompressobj()

        self._parser = GatewayParser()
        self._mapper = GatewayMapper()

    async def connect(self) -> None:
        """Open Gateway WebSocket connection."""

        if self._connected:
            raise RuntimeError("Already connected")

        self._should_reconnect = True

        self._session = aiohttp.ClientSession()

        try:
            self.ws = await self._session.ws_connect(self.GATEWAY_URL)
        except Exception:
            await self._session.close()
            self._session = None
            raise

        self._connected = True

        self._receive_task = asyncio.create_task(
            self._receive_loop()
        )

    async def disconnect(self) -> None:
        """Close Gateway WebSocket connection."""

        self._should_reconnect = False
        self._connected = False

        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        if self.ws is not None and not self.ws.closed:
            await self.ws.close()

        self.ws = None

        if self._session is not None:
            await self._session.close()
            self._session = None

    async def is_connected(self) -> bool:
        """Return whether the Gateway connection is active."""

        return (
            self._connected
            and self.ws is not None
            and not self.ws.closed
        )

    async def send_heartbeat(self) -> None:
        """Send Gateway heartbeat."""

        if self.ws is None or self.ws.closed:
            return

        payload = {
            "op": Opcode.HEARTBEAT,
            "d": self._sequence,
        }

        await self.ws.send_json(payload)

    async def on(
        self,
        event_type: type[DomainEvent],
        handler: EventCallback,
    ) -> None:
        """
        Register a domain event handler.

        Handlers are indexed by domain event class name.
        """

        event_name = event_type.__name__

        handlers = self._event_handlers.setdefault(event_name, [])
        handlers.append(handler)

    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch a domain event to registered handlers."""

        event_name = type(event).__name__
        handlers = self._event_handlers.get(event_name, [])

        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:
                print(f"Error in event handler: {exc}")

    async def _receive_loop(self) -> None:
        """Receive and process Gateway WebSocket messages."""

        while self._should_reconnect and self.ws is not None:
            try:
                msg = await self.ws.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    if isinstance(data, dict):
                        await self._handle_payload(data)

                elif msg.type == aiohttp.WSMsgType.BINARY:
                    decompressed = self._decompress_buffer.decompress(msg.data)

                    if decompressed:
                        data = json.loads(
                            decompressed.decode("utf-8")
                        )

                        if isinstance(data, dict):
                            await self._handle_payload(data)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(
                        f"WebSocket error: {self.ws.exception()}"
                    )
                    break

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print("WebSocket closed by server")
                    break

            except asyncio.CancelledError:
                break

            except Exception as exc:
                print(f"Error in receive loop: {exc}")
                break

    async def _handle_payload(
        self,
        data: dict[str, object],
    ) -> None:
        """
        Handle a Discord Gateway envelope.

        The envelope itself is intentionally kept as raw transport data.
        Event-specific payloads are passed to GatewayParser.
        """

        opcode = self._get_int(data, "op")
        sequence = self._get_int(data, "s")
        event_type = self._get_str(data, "t")

        if sequence is not None:
            self._sequence = sequence

        if opcode == Opcode.HELLO:
            await self._handle_hello(data)
            return

        if opcode == Opcode.HEARTBEAT_ACK:
            return

        if opcode == Opcode.INVALID_SESSION:
            await self.disconnect()
            return

        if opcode != Opcode.DISPATCH:
            return

        if event_type is None:
            return

        payload = data.get("d")

        if not isinstance(payload, dict):
            return

        await self._handle_event(event_type, payload)

    async def _handle_hello(
        self,
        data: dict[str, object],
    ) -> None:
        """Handle Gateway HELLO event."""

        payload = data.get("d")

        if not isinstance(payload, dict):
            raise ValueError("HELLO payload must be an object")

        heartbeat_interval = payload.get("heartbeat_interval")

        if not isinstance(heartbeat_interval, int):
            raise ValueError(
                "HELLO payload is missing heartbeat_interval"
            )

        self._heartbeat_interval = heartbeat_interval

        await self._identify()

        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()

        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop()
        )

    async def _handle_event(
        self,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        """
        Parse a Gateway dispatch payload and map it to a domain event.
        """

        if event_type == GatewayEvent.MESSAGE_CREATE:
            gateway_event = self._parser.parse_message_create(payload)
            domain_event = self._mapper.map_message_create(
                gateway_event
            )

        elif event_type == GatewayEvent.MESSAGE_UPDATE:
            gateway_event = self._parser.parse_message_update(payload)
            domain_event = self._mapper.map_message_update(
                gateway_event
            )

        elif event_type == GatewayEvent.MESSAGE_DELETE:
            gateway_event = self._parser.parse_message_delete(payload)
            domain_event = self._mapper.map_message_delete(
                gateway_event
            )

        elif event_type == GatewayEvent.MESSAGE_REACTION_ADD:
            gateway_event = self._parser.parse_reaction_add(payload)
            domain_event = self._mapper.map_reaction_added(
                gateway_event
            )

        elif event_type == GatewayEvent.MESSAGE_REACTION_REMOVE:
            gateway_event = self._parser.parse_reaction_remove(payload)
            domain_event = self._mapper.map_reaction_removed(
                gateway_event
            )

        elif event_type == GatewayEvent.PRESENCE_UPDATE:
            gateway_event = self._parser.parse_presence_update(payload)
            domain_event = self._mapper.map_presence_update(
                gateway_event
            )

        else:
            return

        await self.dispatch(domain_event)

    async def _identify(self) -> None:
        """Send Gateway IDENTIFY payload."""

        if self.ws is None or self.ws.closed:
            raise RuntimeError(
                "Cannot identify without an active Gateway connection"
            )

        payload = {
            "op": Opcode.IDENTIFY,
            "d": {
                "token": self.token,
                "intents": 513,
                "properties": {
                    "os": "linux",
                    "browser": "aeoncord",
                    "device": "aeoncord",
                },
            },
        }

        await self.ws.send_json(payload)

    async def _heartbeat_loop(self) -> None:
        """Send Gateway heartbeats at the requested interval."""

        while self._should_reconnect:
            try:
                await asyncio.sleep(
                    self._heartbeat_interval / 1000
                )

                await self.send_heartbeat()

            except asyncio.CancelledError:
                break

            except Exception as exc:
                print(f"Heartbeat error: {exc}")
                break

    @staticmethod
    def _get_int(
        data: dict[str, object],
        key: str,
    ) -> int | None:
        value = data.get(key)

        if isinstance(value, int):
            return value

        return None

    @staticmethod
    def _get_str(
        data: dict[str, object],
        key: str,
    ) -> str | None:
        value = data.get(key)

        if isinstance(value, str):
            return value

        return None
