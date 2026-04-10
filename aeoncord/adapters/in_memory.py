"""
In-Memory Adapters.
"""

from __future__ import annotations

from typing import Optional, Callable, Any
from datetime import datetime
import logging

from aeoncord.core.domain.models import (
    Message, MessageId, User, UserId, ChannelId, Channel, Guild, GuildId,
    Role, RoleId, DomainEvent
)
from aeoncord.core.ports import (
    MessageRepository, UserRepository, ChannelRepository,
    GuildRepository, RoleRepository, EventBus, Logger
)


class InMemoryMessageRepository(MessageRepository):
    def __init__(self):
        self._messages: dict[MessageId, Message] = {}

    async def get_by_id(self, message_id: MessageId) -> Optional[Message]:
        return self._messages.get(message_id)

    async def get_many_by_channel(
        self,
        channel_id: ChannelId,
        limit: int = 100,
        before: Optional[MessageId] = None,
    ) -> list[Message]:
        messages = [
            m for m in self._messages.values()
            if m.channel_id == channel_id and not m.is_deleted()
        ]
        messages.sort(key=lambda m: m.created_at, reverse=True)
        return messages[:limit]

    async def save(self, message: Message) -> None:
        self._messages[message.id] = message

    async def delete(self, message_id: MessageId) -> None:
        if message_id in self._messages:
            del self._messages[message_id]

    def clear(self) -> None:
        self._messages.clear()


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users: dict[UserId, User] = {}
        self._current_user: Optional[User] = None

    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        return self._users.get(user_id)

    async def get_current_user(self) -> User:
        if not self._current_user:
            raise ValueError("Current user not set")
        return self._current_user

    async def save(self, user: User) -> None:
        self._users[user.id] = user

    def set_current_user(self, user: User) -> None:
        self._current_user = user


class InMemoryChannelRepository(ChannelRepository):
    def __init__(self):
        self._channels: dict[ChannelId, Channel] = {}

    async def get_by_id(self, channel_id: ChannelId) -> Optional[Channel]:
        return self._channels.get(channel_id)

    async def get_many_by_guild(self, guild_id: GuildId) -> list[Channel]:
        return [c for c in self._channels.values() if c.guild_id == guild_id]

    async def save(self, channel: Channel) -> None:
        self._channels[channel.id] = channel


class InMemoryGuildRepository(GuildRepository):
    def __init__(self):
        self._guilds: dict[GuildId, Guild] = {}

    async def get_by_id(self, guild_id: GuildId) -> Optional[Guild]:
        return self._guilds.get(guild_id)

    async def get_user_guilds(self, user_id: UserId) -> list[Guild]:
        return list(self._guilds.values())

    async def save(self, guild: Guild) -> None:
        self._guilds[guild.id] = guild


class InMemoryRoleRepository(RoleRepository):
    def __init__(self):
        self._roles: dict[RoleId, Role] = {}

    async def get_by_id(self, role_id: RoleId) -> Optional[Role]:
        return self._roles.get(role_id)

    async def get_many_by_guild(self, guild_id: GuildId) -> list[Role]:
        return [r for r in self._roles.values() if r.guild_id == guild_id]

    async def save(self, role: Role) -> None:
        self._roles[role.id] = role


class InMemoryEventBus(EventBus):
    """
    B U S
    """

    def __init__(self):
        self._subscribers: dict[type, list[Callable]] = {}

    async def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._subscribers.get(type(event), [])

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")


class SimpleLogger(Logger):
    def __init__(self, name: str = "aeoncord"):
        self.logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs: any) -> None:
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs: any) -> None:
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: any) -> None:
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: any) -> None:
        self.logger.error(message, extra=kwargs)
