"""
These are abstract interfaces that define contracts between domain and adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from aeoncord.core.domain.models import (
    Channel,
    ChannelId,
    DomainEvent,
    Guild,
    GuildId,
    Message,
    MessageId,
    Role,
    RoleId,
    User,
    UserId,
)


class MessageRepository(ABC):
    @abstractmethod
    async def get_by_id(self, message_id: MessageId) -> Optional[Message]:
        pass

    @abstractmethod
    async def get_many_by_channel(
        self,
        channel_id: ChannelId,
        limit: int = 100,
        before: Optional[MessageId] = None,
    ) -> list[Message]:
        pass

    @abstractmethod
    async def save(self, message: Message) -> None:
        pass

    @abstractmethod
    async def delete(self, message_id: MessageId) -> None:
        pass


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        pass

    @abstractmethod
    async def get_current_user(self) -> User:
        pass

    @abstractmethod
    async def save(self, user: User) -> None:
        pass


class ChannelRepository(ABC):
    @abstractmethod
    async def get_by_id(self, channel_id: ChannelId) -> Optional[Channel]:
        pass

    @abstractmethod
    async def get_many_by_guild(self, guild_id: GuildId) -> list[Channel]:
        pass

    @abstractmethod
    async def save(self, channel: Channel) -> None:
        pass


class GuildRepository(ABC):
    @abstractmethod
    async def get_by_id(self, guild_id: GuildId) -> Optional[Guild]:
        pass

    @abstractmethod
    async def get_user_guilds(self, user_id: UserId) -> list[Guild]:
        pass

    @abstractmethod
    async def save(self, guild: Guild) -> None:
        pass


class RoleRepository(ABC):

    @abstractmethod
    async def get_by_id(self, role_id: RoleId) -> Optional[Role]:
        pass

    @abstractmethod
    async def get_many_by_guild(self, guild_id: GuildId) -> list[Role]:
        pass

    @abstractmethod
    async def save(self, role: Role) -> None:
        pass


class EventBus(ABC):
    @abstractmethod
    async def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        pass

    @abstractmethod
    async def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        pass

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        pass


class Logger(ABC):
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        pass


class GatewayConnection(ABC):
    """
    WebSocket gateway connection.
    """

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        pass

    @abstractmethod
    async def send_heartbeat(self) -> None:
        pass


class EventHandler(ABC):
    """
    Event dispatcher.
    """

    @abstractmethod
    async def on(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        pass

    @abstractmethod
    async def dispatch(self, event: DomainEvent) -> None:
        pass


class HTTPClient(ABC):
    """
    HTTP com with d.api.
    """

    @abstractmethod
    async def get(self, endpoint: str, **kwargs: Any) -> dict | list:
        pass

    @abstractmethod
    async def post(self, endpoint: str, data: dict | None = None, **kwargs: Any) -> dict:
        pass

    @abstractmethod
    async def patch(self, endpoint: str, data: dict | None = None, **kwargs: Any) -> dict:
        pass

    @abstractmethod
    async def delete(self, endpoint: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    async def put(self, endpoint: str, data: dict | None = None, **kwargs: Any) -> dict:
        pass


class EntityMapper(ABC):
    @abstractmethod
    def to_domain(self, data: dict) -> Any:
        pass

    @abstractmethod
    def from_domain(self, entity: Any) -> dict:
        pass
