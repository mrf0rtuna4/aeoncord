"""
Discord Gateway internal models.

These models represent validated Gateway data.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GatewayMessageCreate:
    id: str
    channel_id: str
    guild_id: str | None
    author_id: str
    content: str


@dataclass(slots=True, frozen=True)
class GatewayMessageUpdate:
    id: str
    channel_id: str | None
    guild_id: str | None
    author_id: str | None
    content: str | None
    edited_timestamp: str | None


@dataclass(slots=True, frozen=True)
class GatewayMessageDelete:
    id: str
    channel_id: str
    guild_id: str | None


@dataclass(slots=True, frozen=True)
class GatewayReaction:
    message_id: str
    user_id: str
    emoji: str


@dataclass(slots=True, frozen=True)
class GatewayPresenceUpdate:
    user_id: str
    status: str
