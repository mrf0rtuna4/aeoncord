"""
Discord Gateway payload type definitions.
"""

from __future__ import annotations

from typing import TypedDict


class UserPayload(TypedDict):
    id: str


class EmojiPayload(TypedDict):
    name: str


class AuthorPayload(TypedDict):
    id: str


class GatewayPayload(TypedDict):
    op: int
    d: object
    s: int | None
    t: str | None


class HelloPayload(TypedDict):
    heartbeat_interval: int


class IdentifyProperties(TypedDict):
    os: str
    browser: str
    device: str


class IdentifyData(TypedDict):
    token: str
    intents: int
    properties: IdentifyProperties


class IdentifyPayload(TypedDict):
    op: int
    d: IdentifyData


class MessageCreatePayload(TypedDict):
    id: str
    channel_id: str
    content: str
    author: AuthorPayload
    guild_id: str | None


class MessageUpdatePayload(TypedDict, total=False):
    id: str
    channel_id: str
    guild_id: str
    content: str
    author: AuthorPayload
    edited_timestamp: str


class MessageDeletePayload(TypedDict):
    id: str
    channel_id: str
    guild_id: str | None


class ReactionAddPayload(TypedDict):
    message_id: str
    user_id: str
    emoji: EmojiPayload


class ReactionRemovePayload(TypedDict):
    message_id: str
    user_id: str
    emoji: EmojiPayload


class PresenceUserPayload(TypedDict):
    id: str


class PresenceUpdatePayload(TypedDict, total=False):
    user: PresenceUserPayload
    status: str

GatewayEventPayload = (
    MessageCreatePayload
    | MessageUpdatePayload
    | MessageDeletePayload
    | ReactionAddPayload
    | ReactionRemovePayload
    | PresenceUpdatePayload
)