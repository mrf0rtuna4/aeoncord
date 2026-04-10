"""
Discord Gateway (WebSocket) Adapter.
"""

from __future__ import annotations

import json
import asyncio
import zlib
from typing import Any, Optional, Callable
from datetime import datetime, timedelta

import aiohttp

from aeoncord.core.domain.models import (
    DomainEvent, MessageCreated, MessageEdited, MessageDeleted,
    ReactionAdded, ReactionRemoved, UserOnline, UserOffline,
    MessageId, UserId, ChannelId, GuildId
)
from aeoncord.core.ports import GatewayConnection, EventHandler


class Opcode:
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
    WebSocket connection.
    """

    GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json&compression=zlib-stream"

    def __init__(self, token: str):
        self.token = token
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connected = False
        self._session_id: Optional[str] = None
        self._sequence: int = 0
        self._heartbeat_interval: int = 0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._event_handlers: dict[str, list[Callable]] = {}
        self._decompress_buffer = zlib.decompressobj()
        self._should_reconnect = True

    async def connect(self) -> None:
        if self._connected:
            raise RuntimeError("Already connected")

        session = aiohttp.ClientSession()
        self.ws = await session.ws_connect(self.GATEWAY_URL)
        self._connected = True

        asyncio.create_task(self._receive_loop())

    async def disconnect(self) -> None:
        self._should_reconnect = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self.ws:
            await self.ws.close()

        self._connected = False

    async def is_connected(self) -> bool:
        return self._connected and self.ws and not self.ws.closed

    async def send_heartbeat(self) -> None:
        if not self.ws:
            return

        payload = {
            "op": Opcode.HEARTBEAT,
            "d": self._sequence,
        }
        await self.ws.send_json(payload)

    async def on(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        event_name = event_type.__name__
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)

    async def dispatch(self, event: DomainEvent) -> None:
        event_name = type(event).__name__
        handlers = self._event_handlers.get(event_name, [])

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

    async def _receive_loop(self) -> None:
        while self._should_reconnect and self.ws:
            try:
                msg = await self.ws.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_payload(data)

                elif msg.type == aiohttp.WSMsgType.BINARY:
                    decompressed = self._decompress_buffer.decompress(msg.data)
                    if decompressed:
                        data = json.loads(decompressed.decode("utf-8"))
                        await self._handle_payload(data)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WebSocket error: {self.ws.exception()}")
                    break

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print("WebSocket closed by server")
                    break

            except Exception as e:
                print(f"Error in receive loop: {e}")
                break

    async def _handle_payload(self, data: dict[str, Any]) -> None:
        opcode = data.get("op")
        sequence = data.get("s")
        event_type = data.get("t")
        payload = data.get("d")

        if sequence:
            self._sequence = sequence

        if opcode == Opcode.HELLO:
            self._heartbeat_interval = payload["heartbeat_interval"]
            await self._identify()
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        elif opcode == Opcode.HEARTBEAT_ACK:
            pass

        elif opcode == Opcode.INVALID_SESSION:
            await self.disconnect()

        elif opcode == Opcode.DISPATCH:
            await self._handle_event(event_type, payload)

    async def _handle_event(self, event_type: str, payload: dict) -> None:
        if event_type == GatewayEvent.MESSAGE_CREATE:
            event = MessageCreated(
                message_id=MessageId(int(payload["id"])),
                author_id=UserId(int(payload["author"]["id"])),
                channel_id=ChannelId(int(payload["channel_id"])),
                guild_id=GuildId(int(payload["guild_id"])) if payload.get("guild_id") else None,
                content=payload.get("content", ""),
            )
            await self.dispatch(event)

        elif event_type == GatewayEvent.MESSAGE_UPDATE:
            event = MessageEdited(
                message_id=MessageId(int(payload["id"])),
                editor_id=UserId(int(payload["author"]["id"])) if payload.get("author") else UserId(0),
                new_content=payload.get("content", ""),
                edited_at=datetime.fromisoformat(
                    payload["edited_timestamp"].replace("Z", "+00:00")
                ),
            )
            await self.dispatch(event)

        elif event_type == GatewayEvent.MESSAGE_DELETE:
            event = MessageDeleted(
                message_id=MessageId(int(payload["id"])),
                channel_id=ChannelId(int(payload["channel_id"])),
                deleter_id=None,
            )
            await self.dispatch(event)

        elif event_type == GatewayEvent.MESSAGE_REACTION_ADD:
            event = ReactionAdded(
                message_id=MessageId(int(payload["message_id"])),
                user_id=UserId(int(payload["user_id"])),
                emoji=payload.get("emoji", {}).get("name", "unknown"),
            )
            await self.dispatch(event)

        elif event_type == GatewayEvent.MESSAGE_REACTION_REMOVE:
            event = ReactionRemoved(
                message_id=MessageId(int(payload["message_id"])),
                user_id=UserId(int(payload["user_id"])),
                emoji=payload.get("emoji", {}).get("name", "unknown"),
            )
            await self.dispatch(event)

        elif event_type == GatewayEvent.PRESENCE_UPDATE:
            user_data = payload.get("user", {})
            status = payload.get("status")  # onl, idl, dnd, inv

            user_id = UserId(int(user_data["id"]))
            if status == "offline":
                event = UserOffline(user_id=user_id, timestamp=datetime.now())
            else:
                event = UserOnline(user_id=user_id, timestamp=datetime.now())

            await self.dispatch(event)

    async def _identify(self) -> None:
        payload = {
            "op": Opcode.IDENTIFY,
            "d": {
                "token": self.token,
                "intents": 513,  # GUILDS | GUILD_MESSAGES | DIRECT_MESSAGES
                "properties": {
                    "os": "linux",
                    "browser": "aeoncord",
                    "device": "aeoncord",
                },
            },
        }
        await self.ws.send_json(payload)

    async def _heartbeat_loop(self) -> None:
        while self._should_reconnect:
            try:
                await asyncio.sleep(self._heartbeat_interval / 1000)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break
