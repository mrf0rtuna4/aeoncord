"""
Core domain models for aeoncord.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for all value objects."""

    pass


@dataclass(frozen=True)
class UserId(ValueObject):
    value: int

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class MessageId(ValueObject):
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ChannelId(ValueObject):
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class GuildId(ValueObject):
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class RoleId(ValueObject):
    value: int


@dataclass(frozen=True)
class Snowflake(ValueObject):
    value: int

    def to_timestamp(self) -> datetime:
        """Extract Unix timestamp from snowflake (milliseconds since 2015-01-01)."""
        discord_epoch = 1420070400000
        timestamp_ms = (self.value >> 22) + discord_epoch
        return datetime.fromtimestamp(timestamp_ms / 1000)


@dataclass(frozen=True)
class Mention(ValueObject):
    user_id: Optional[UserId] = None
    role_id: Optional[RoleId] = None
    channel_id: Optional[ChannelId] = None
    guild_id: Optional[GuildId] = None

    def is_valid(self) -> bool:
        return any([self.user_id, self.role_id, self.channel_id, self.guild_id])


class MessageType(str, Enum):
    DEFAULT = "default"
    RECIPIENT_ADD = "recipient_add"
    RECIPIENT_REMOVE = "recipient_remove"
    CALL = "call"
    CHANNEL_NAME_CHANGE = "channel_name_change"
    CHANNEL_ICON_CHANGE = "channel_icon_change"
    CHANNEL_PINNED_MESSAGE = "channel_pinned_message"
    USER_JOIN = "user_join"
    GUILD_BOOST = "guild_boost"
    GUILD_BOOST_TIER_1 = "guild_boost_tier_1"
    GUILD_BOOST_TIER_2 = "guild_boost_tier_2"
    GUILD_BOOST_TIER_3 = "guild_boost_tier_3"
    CHANNEL_FOLLOW_ADD = "channel_follow_add"
    GUILD_DISCOVERY_DISQUALIFIED = "guild_discovery_disqualified"
    GUILD_DISCOVERY_REQUALIFIED = "guild_discovery_requalified"
    GUILD_DISCOVERY_GRACE_PERIOD_INITIAL_WARNING = "guild_discovery_grace_period_initial_warning"
    GUILD_DISCOVERY_GRACE_PERIOD_FINAL_WARNING = "guild_discovery_grace_period_final_warning"
    THREAD_CREATED = "thread_created"
    REPLY = "reply"
    CHAT_INPUT_COMMAND = "chat_input_command"
    THREAD_STARTER_MESSAGE = "thread_starter_message"
    GUILD_INVITE_REMINDER = "guild_invite_reminder"
    CONTEXT_MENU_COMMAND = "context_menu_command"
    AUTO_MODERATION_ACTION = "auto_moderation_action"


@dataclass(frozen=True)
class Embed(ValueObject):
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[int] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    author_name: Optional[str] = None
    author_icon_url: Optional[str] = None
    footer_text: Optional[str] = None
    footer_icon_url: Optional[str] = None

    def is_valid(self) -> bool:
        return bool(self.title or self.description)


@dataclass
class User:
    id: UserId
    username: str
    avatar_hash: Optional[str]
    is_bot: bool
    is_system: bool
    locale: Optional[str]
    verified: bool
    email: Optional[str]
    mfa_enabled: bool
    premium_type: int  # 0 = None, 1 = Nitro Classic, 2 = Nitro
    public_flags: int

    def display_name(self) -> str:
        return f"{self.username}"

    def is_official_bot(self) -> bool:
        return self.is_bot and self.is_system


@dataclass
class Message:
    id: MessageId
    channel_id: ChannelId
    guild_id: Optional[GuildId]
    author_id: UserId
    author: User
    content: str
    created_at: datetime
    edited_at: Optional[datetime]
    is_pinned: bool
    is_tts: bool
    message_type: MessageType
    embeds: list[Embed] = field(default_factory=list)
    mentions: list[UserId] = field(default_factory=list)
    mention_roles: list[RoleId] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)  # URLs
    reactions: dict[str, int] = field(default_factory=dict)  # emoji -> count
    _is_deleted: bool = field(default=False, init=False)

    def can_delete(self, requester_id: UserId, is_admin: bool = False) -> bool:
        if self._is_deleted:
            return False
        return requester_id == self.author_id or is_admin

    def can_edit(self, requester_id: UserId) -> bool:
        if self._is_deleted:
            return False
        return requester_id == self.author_id

    def can_react(self) -> bool:
        return not self._is_deleted

    def mark_deleted(self) -> None:
        self._is_deleted = True

    def is_deleted(self) -> bool:
        return self._is_deleted

    def add_mention(self, user_id: UserId) -> None:
        if user_id not in self.mentions:
            self.mentions.append(user_id)

    def add_reaction(self, emoji: str) -> None:
        self.reactions[emoji] = self.reactions.get(emoji, 0) + 1

    def remove_reaction(self, emoji: str) -> None:
        if emoji in self.reactions:
            self.reactions[emoji] -= 1
            if self.reactions[emoji] <= 0:
                del self.reactions[emoji]

    def content_length(self) -> int:
        return len(self.content)

    def is_empty(self) -> bool:
        has_text = bool(self.content.strip())
        has_embeds = bool(self.embeds)
        has_attachments = bool(self.attachments)
        return not (has_text or has_embeds or has_attachments)


@dataclass
class Channel:
    """Represents a Discord channel."""

    id: ChannelId
    guild_id: Optional[GuildId]
    name: str
    position: int
    topic: Optional[str]
    is_nsfw: bool
    is_private: bool
    owner_id: Optional[UserId]
    created_at: datetime

    def is_dm(self) -> bool:
        return self.guild_id is None


@dataclass
class Guild:
    """Represents a Discord guild."""

    id: GuildId
    name: str
    icon_hash: Optional[str]
    owner_id: UserId
    region: str
    member_count: int
    created_at: datetime

    def get_member_count(self) -> int:
        return self.member_count


@dataclass
class Role:
    """Represents a Discord role within a guild."""

    id: RoleId
    guild_id: GuildId
    name: str
    color: int
    position: int
    permissions: int  # Bitfield
    is_hoisted: bool
    is_managed: bool
    is_mentionable: bool


@dataclass
class DomainEvent(ABC):
    event_id: UUID = field(default_factory=uuid4, init=False)
    occurred_at: datetime = field(default_factory=datetime.now, init=False)


@dataclass
class MessageCreated(DomainEvent):
    message_id: MessageId
    author_id: UserId
    channel_id: ChannelId
    guild_id: Optional[GuildId] = None
    content: str = ""


@dataclass
class MessageEdited(DomainEvent):
    message_id: MessageId
    editor_id: UserId
    edited_at: datetime
    new_content: str = ""


@dataclass
class MessageDeleted(DomainEvent):
    message_id: MessageId
    channel_id: ChannelId
    deleter_id: Optional[UserId] = None


@dataclass
class ReactionAdded(DomainEvent):
    message_id: MessageId
    user_id: UserId
    emoji: str = ""


@dataclass
class ReactionRemoved(DomainEvent):
    message_id: MessageId
    user_id: UserId
    emoji: str = ""


@dataclass
class UserOnline(DomainEvent):
    user_id: UserId
    timestamp: datetime


@dataclass
class UserOffline(DomainEvent):
    user_id: UserId
    timestamp: datetime
