"""
Event DTOs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from aeoncord.core.domain.models import ChannelId, Embed, GuildId, Message, MessageId, User, UserId


@dataclass
class MessageCreateEvent:
    id: MessageId
    author: User
    channel_id: ChannelId
    guild_id: Optional[GuildId]
    content: str
    created_at: datetime
    embeds: list[Embed]
    attachments: list[str]

    _message: Message

    async def reply(self, content: str) -> Message:
        pass

    async def react(self, emoji: str) -> None:
        pass

    async def delete(self) -> None:
        pass

    async def edit(self, new_content: str) -> Message:
        pass


@dataclass
class MessageUpdateEvent:
    id: MessageId
    channel_id: ChannelId
    new_content: str
    edited_at: datetime


@dataclass
class MessageDeleteEvent:
    id: MessageId
    channel_id: ChannelId
    guild_id: Optional[GuildId]


@dataclass
class MessageBulkDeleteEvent:
    channel_id: ChannelId
    message_ids: list[MessageId]


@dataclass
class ReactionAddEvent:
    message_id: MessageId
    user_id: UserId
    emoji: str
    channel_id: ChannelId
    guild_id: Optional[GuildId]


@dataclass
class ReactionRemoveEvent:
    message_id: MessageId
    user_id: UserId
    emoji: str
    channel_id: ChannelId
    guild_id: Optional[GuildId]


@dataclass
class ReactionRemoveAllEvent:
    message_id: MessageId
    channel_id: ChannelId
    guild_id: Optional[GuildId]


@dataclass
class ReactionRemoveEmojiEvent:
    message_id: MessageId
    emoji: str
    channel_id: ChannelId
    guild_id: Optional[GuildId]


@dataclass
class UserOnlineEvent:
    user_id: UserId
    timestamp: datetime


@dataclass
class UserOfflineEvent:
    user_id: UserId
    timestamp: datetime


@dataclass
class UserUpdateEvent:
    user_id: UserId
    user: User


@dataclass
class TypingStartEvent:
    user_id: UserId
    channel_id: ChannelId
    guild_id: Optional[GuildId]
    timestamp: datetime


@dataclass
class ChannelCreateEvent:
    channel_id: ChannelId
    guild_id: Optional[GuildId]
    name: str


@dataclass
class ChannelUpdateEvent:
    channel_id: ChannelId
    guild_id: Optional[GuildId]
    name: str


@dataclass
class ChannelDeleteEvent:
    channel_id: ChannelId
    guild_id: Optional[GuildId]


@dataclass
class ChannelPinsUpdateEvent:
    channel_id: ChannelId
    guild_id: Optional[GuildId]
    last_pin_timestamp: Optional[datetime]


@dataclass
class GuildCreateEvent:
    guild_id: GuildId
    name: str


@dataclass
class GuildUpdateEvent:
    guild_id: GuildId
    name: str


@dataclass
class GuildDeleteEvent:
    guild_id: GuildId


@dataclass
class GuildMemberAddEvent:
    guild_id: GuildId
    user_id: UserId
    joined_at: datetime


@dataclass
class GuildMemberRemoveEvent:
    guild_id: GuildId
    user_id: UserId


@dataclass
class GuildMemberUpdateEvent:
    guild_id: GuildId
    user_id: UserId


@dataclass
class GuildBanAddEvent:
    guild_id: GuildId
    user_id: UserId


@dataclass
class GuildBanRemoveEvent:
    guild_id: GuildId
    user_id: UserId


@dataclass
class GuildRoleCreateEvent:
    guild_id: GuildId
    role_id: GuildId
    name: str


@dataclass
class GuildRoleUpdateEvent:
    guild_id: GuildId
    role_id: GuildId
    name: str


@dataclass
class GuildRoleDeleteEvent:
    guild_id: GuildId
    role_id: GuildId


@dataclass
class ReadyEvent:
    timestamp: datetime
    bot_user: User


@dataclass
class ResumedEvent:
    timestamp: datetime


@dataclass
class DisconnectEvent:
    timestamp: datetime
    reason: Optional[str] = None


@dataclass
class ReconnectEvent:
    timestamp: datetime
