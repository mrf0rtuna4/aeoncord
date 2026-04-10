"""
Discord REST API Adapter.
"""

from __future__ import annotations

import json
from typing import Any, Optional
from datetime import datetime

import aiohttp

from aeoncord.core.domain.models import (
    Message, MessageId, User, UserId, ChannelId, Channel, Guild, GuildId,
    Role, RoleId, MessageType, Embed
)
from aeoncord.core.ports import HTTPClient, EntityMapper, MessageRepository


class DiscordHTTPClient(HTTPClient):
    """
    Concrete HTTP client.
    """

    BASE_URL = "https://discord.com/api/v10"

    def __init__(self, token: str):
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "Aeoncord/0.1.0",
        }

    async def __aenter__(self) -> DiscordHTTPClient:
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            await self.session.close()

    async def get(self, endpoint: str, **kwargs: Any) -> dict | list:
        url = f"{self.BASE_URL}{endpoint}"
        if not self.session:
            raise RuntimeError(
                "HTTPClient not initialized. Use async context manager.")

        async with self.session.get(url, headers=self.headers, **kwargs) as resp:
            await self._handle_response(resp)
            return await resp.json()

    async def post(self, endpoint: str, data: dict | None = None, **kwargs: Any) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        if not self.session:
            raise RuntimeError(
                "HTTPClient not initialized. Use async context manager.")

        async with self.session.post(
            url,
            headers=self.headers,
            data=json.dumps(data) if data else None,
            **kwargs
        ) as resp:
            await self._handle_response(resp)
            return await resp.json()

    async def patch(self, endpoint: str, data: dict | None = None, **kwargs: Any) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        if not self.session:
            raise RuntimeError(
                "HTTPClient not initialized. Use async context manager.")

        async with self.session.patch(
            url,
            headers=self.headers,
            data=json.dumps(data) if data else None,
            **kwargs
        ) as resp:
            await self._handle_response(resp)
            return await resp.json()

    async def delete(self, endpoint: str, **kwargs: Any) -> None:
        url = f"{self.BASE_URL}{endpoint}"
        if not self.session:
            raise RuntimeError(
                "HTTPClient not initialized. Use async context manager.")

        async with self.session.delete(url, headers=self.headers, **kwargs) as resp:
            await self._handle_response(resp)

    async def put(self, endpoint: str, data: dict | None = None, **kwargs: Any) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        if not self.session:
            raise RuntimeError(
                "HTTPClient not initialized. Use async context manager.")

        async with self.session.put(
            url,
            headers=self.headers,
            data=json.dumps(data) if data else None,
            **kwargs
        ) as resp:
            await self._handle_response(resp)
            return await resp.json()

    async def _handle_response(self, resp: aiohttp.ClientResponse) -> None:
        if resp.status == 401:
            raise ValueError("Invalid or expired token")
        elif resp.status == 403:
            raise PermissionError("Forbidden - insufficient permissions")
        elif resp.status == 404:
            raise ValueError("Resource not found")
        elif resp.status == 429:
            raise RuntimeError("Rate limited by Discord")
        elif resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status}: {resp.reason}")


class MessageMapper(EntityMapper):

    async def to_domain(self, user_repo: UserRepository, data: dict) -> Message:
        author_data = data.get("author", {})
        author = await user_repo.get_by_id(UserId(int(author_data["id"])))

        embeds = []
        for embed_data in data.get("embeds", []):
            embeds.append(Embed(
                title=embed_data.get("title"),
                description=embed_data.get("description"),
                url=embed_data.get("url"),
                color=embed_data.get("color"),
                image_url=embed_data.get("image", {}).get("url"),
                thumbnail_url=embed_data.get("thumbnail", {}).get("url"),
                author_name=embed_data.get("author", {}).get("name"),
                author_icon_url=embed_data.get("author", {}).get("icon_url"),
                footer_text=embed_data.get("footer", {}).get("text"),
                footer_icon_url=embed_data.get("footer", {}).get("icon_url"),
            ))

        mentions = [UserId(int(m["id"])) for m in data.get("mentions", [])]
        mention_roles = [RoleId(int(r)) for r in data.get("mention_roles", [])]

        reactions = {}
        for reaction in data.get("reactions", []):
            emoji = reaction.get("emoji", {}).get("name", "unknown")
            count = reaction.get("count", 0)
            reactions[emoji] = count

        return Message(
            id=MessageId(int(data["id"])),
            channel_id=ChannelId(int(data["channel_id"])),
            guild_id=GuildId(int(data["guild_id"])) if data.get(
                "guild_id") else None,
            author_id=UserId(int(author_data["id"])),
            author=author,
            content=data.get("content", ""),
            created_at=datetime.fromisoformat(
                data["timestamp"].replace("Z", "+00:00")),
            edited_at=datetime.fromisoformat(
                data["edited_timestamp"].replace("Z", "+00:00"))
            if data.get("edited_timestamp") else None,
            is_pinned=data.get("pinned", False),
            is_tts=data.get("tts", False),
            message_type=MessageType(data.get("type", "default")),
            embeds=embeds,
            mentions=mentions,
            mention_roles=mention_roles,
            attachments=[a["url"] for a in data.get("attachments", [])],
            reactions=reactions,
        )

    def from_domain(self, message: Message) -> dict:
        return {
            "content": message.content,
            "embeds": [
                {
                    "title": e.title,
                    "description": e.description,
                    "url": e.url,
                    "color": e.color,
                    "image": {"url": e.image_url} if e.image_url else None,
                    "thumbnail": {"url": e.thumbnail_url} if e.thumbnail_url else None,
                    "author": {"name": e.author_name, "icon_url": e.author_icon_url}
                    if e.author_name else None,
                    "footer": {"text": e.footer_text, "icon_url": e.footer_icon_url}
                    if e.footer_text else None,
                }
                for e in message.embeds
            ],
            "tts": message.is_tts,
        }


class DiscordRESTMessageRepository(MessageRepository):
    def __init__(self, http_client: DiscordHTTPClient, mapper: MessageMapper):
        self.http = http_client
        self.mapper = mapper

    async def get_by_id(self, message_id: MessageId) -> Optional[Message]:
        try:
            return None
        except ValueError:
            return None

    async def get_many_by_channel(
        self,
        channel_id: ChannelId,
        limit: int = 100,
        before: Optional[MessageId] = None,
    ) -> list[Message]:
        endpoint = f"/channels/{channel_id.value}/messages"
        params = {"limit": min(limit, 100)}

        if before:
            params["before"] = str(before.value)

        data = await self.http.get(endpoint, params=params)
        return [await self.mapper.to_domain(data) for data in data]

    async def save(self, message: Message) -> None:
        endpoint = f"/channels/{message.channel_id.value}/messages"
        payload = self.mapper.from_domain(message)

        await self.http.post(endpoint, data=payload)

    async def delete(self, message_id: MessageId) -> None:
        pass


class UserMapper(EntityMapper):
    """map discord user"""

    def to_domain(self, data: dict) -> User:
        return User(
            id=UserId(int(data["id"])),
            username=data["username"],
            discriminator=data.get("discriminator", "0000"),
            avatar_hash=data.get("avatar"),
            is_bot=data.get("bot", False),
            is_system=data.get("system", False),
            locale=data.get("locale"),
            verified=data.get("verified", False),
            email=data.get("email"),
            mfa_enabled=data.get("mfa_enabled", False),
            premium_type=data.get("premium_type", 0),
            public_flags=data.get("public_flags", 0),
        )

    def from_domain(self, user: User) -> dict:
        return {
            "id": str(user.id.value),
            "username": user.username,
            "discriminator": user.discriminator,
            "avatar": user.avatar_hash,
            "bot": user.is_bot,
            "system": user.is_system,
            "locale": user.locale,
            "verified": user.verified,
            "email": user.email,
            "mfa_enabled": user.mfa_enabled,
            "premium_type": user.premium_type,
            "public_flags": user.public_flags,
        }
