"""
DiscordClient - Main entry point for aeoncord.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Optional, Type

from aeoncord.adapters.discord_gateway import DiscordGateway
from aeoncord.adapters.discord_rest import DiscordHTTPClient
from aeoncord.adapters.in_memory import (
    InMemoryChannelRepository,
    InMemoryEventBus,
    InMemoryGuildRepository,
    InMemoryMessageRepository,
    InMemoryRoleRepository,
    InMemoryUserRepository,
    SimpleLogger,
)
from aeoncord.core.domain.models import (
    ChannelId,
    Message,
    MessageId,
    UserId,
)
from aeoncord.core.ports import EventBus, Logger, MessageRepository, UserRepository
from aeoncord.core.use_cases import (
    AddReactionUseCase,
    DeleteMessageUseCase,
    EditMessageUseCase,
    RemoveReactionUseCase,
    SendMessageUseCase,
)
from aeoncord.events import (
    MessageCreateEvent,
    MessageDeleteEvent,
    MessageUpdateEvent,
    ReactionAddEvent,
    UserOnlineEvent,
)


@dataclass
class ClientConfig:
    token: str
    intents: int = 513
    auto_sync_commands: bool = True
    debug: bool = False


class DiscordClient:
    def __init__(
        self,
        token: str,
        *,
        intents: int = 513,
        auto_sync_commands: bool = True,
        debug: bool = False,
    ):
        self.config = ClientConfig(
            token=token,
            intents=intents,
            auto_sync_commands=auto_sync_commands,
            debug=debug,
        )

        self._logger = SimpleLogger("aeoncord.client")
        self._message_repo: MessageRepository = InMemoryMessageRepository()
        self._user_repo: UserRepository = InMemoryUserRepository()
        self._channel_repo = InMemoryChannelRepository()
        self._guild_repo = InMemoryGuildRepository()
        self._role_repo = InMemoryRoleRepository()
        self._event_bus: EventBus = InMemoryEventBus()

        self._http: Optional[DiscordHTTPClient] = None

        self._gateway: Optional[DiscordGateway] = None

        self._send_message = SendMessageUseCase(
            self._message_repo,
            self._event_bus,
            self._logger,
        )
        self._edit_message = EditMessageUseCase(
            self._message_repo,
            self._event_bus,
            self._logger,
        )
        self._delete_message = DeleteMessageUseCase(
            self._message_repo,
            self._event_bus,
            self._logger,
        )
        self._add_reaction = AddReactionUseCase(
            self._message_repo,
            self._event_bus,
            self._logger,
        )
        self._remove_reaction = RemoveReactionUseCase(
            self._message_repo,
            self._event_bus,
            self._logger,
        )

        self._event_handlers: dict[Type, list[Callable]] = {}

    async def connect(self) -> None:
        try:
            self._logger.info("Connecting to Discord...")

            self._http = DiscordHTTPClient(self.config.token)

            self._gateway = DiscordGateway(self.config.token)
            await self._gateway.connect()

            await self._register_gateway_handlers()

            self._logger.info("Connected to Discord!")

        except Exception as e:
            self._logger.error(f"Connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        if self._gateway:
            await self._gateway.disconnect()
        self._logger.info("Disconnected from Discord")

    async def is_connected(self) -> bool:
        if not self._gateway:
            return False
        return await self._gateway.is_connected()

    def on(self, event_type: Type[Any]) -> Callable:

        def decorator(func: Callable) -> Callable:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(func)
            return func

        return decorator

    async def _dispatch_event(self, event: Any) -> None:
        handlers = self._event_handlers.get(type(event), [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self._logger.error(f"Error in event handler: {e}")

    async def _register_gateway_handlers(self) -> None:
        if not self._gateway:
            return

        from aeoncord.core.domain.models import (
            MessageCreated,
            MessageDeleted,
            MessageEdited,
            ReactionAdded,
            UserOnline,
        )

        async def handle_message_created(event: MessageCreated) -> None:
            app_event = MessageCreateEvent(
                id=event.message_id,
                author=None,
                channel_id=event.channel_id,
                guild_id=event.guild_id,
                content=event.content,
                created_at=event.occurred_at,
                embeds=[],
                attachments=[],
                _message=None,
            )
            await self._dispatch_event(app_event)

        async def handle_message_edited(event: MessageEdited) -> None:
            app_event = MessageUpdateEvent(
                id=event.message_id,
                channel_id=None,
                new_content=event.new_content,
                edited_at=event.edited_at,
            )
            await self._dispatch_event(app_event)

        async def handle_message_deleted(event: MessageDeleted) -> None:
            app_event = MessageDeleteEvent(
                id=event.message_id,
                channel_id=event.channel_id,
                guild_id=None,
            )
            await self._dispatch_event(app_event)

        async def handle_reaction_added(event: ReactionAdded) -> None:
            app_event = ReactionAddEvent(
                message_id=event.message_id,
                user_id=event.user_id,
                emoji=event.emoji,
                channel_id=None,
                guild_id=None,
            )
            await self._dispatch_event(app_event)

        async def handle_user_online(event: UserOnline) -> None:
            app_event = UserOnlineEvent(
                user_id=event.user_id,
                timestamp=event.timestamp,
            )
            await self._dispatch_event(app_event)

        await self._gateway.on(MessageCreated, handle_message_created)
        await self._gateway.on(MessageEdited, handle_message_edited)
        await self._gateway.on(MessageDeleted, handle_message_deleted)
        await self._gateway.on(ReactionAdded, handle_reaction_added)
        await self._gateway.on(UserOnline, handle_user_online)

    async def send_message(
        self,
        channel_id: ChannelId,
        content: str,
    ) -> Message:
        bot_user_id = UserId(0)

        return await self._send_message.execute(
            channel_id=channel_id,
            author_id=bot_user_id,
            content=content,
        )

    async def edit_message(
        self,
        message_id: MessageId,
        new_content: str,
    ) -> Message:
        bot_user_id = UserId(0)

        return await self._edit_message.execute(
            message_id=message_id,
            editor_id=bot_user_id,
            new_content=new_content,
        )

    async def delete_message(self, message_id: MessageId) -> None:
        bot_user_id = UserId(0)

        await self._delete_message.execute(
            message_id=message_id,
            requester_id=bot_user_id,
            is_admin=True,
        )

    async def add_reaction(
        self,
        message_id: MessageId,
        emoji: str,
    ) -> None:
        bot_user_id = UserId(0)

        await self._add_reaction.execute(
            message_id=message_id,
            user_id=bot_user_id,
            emoji=emoji,
        )

    async def remove_reaction(
        self,
        message_id: MessageId,
        emoji: str,
    ) -> None:
        bot_user_id = UserId(0)

        await self._remove_reaction.execute(
            message_id=message_id,
            user_id=bot_user_id,
            emoji=emoji,
        )

    @property
    def message_repo(self) -> MessageRepository:
        return self._message_repo

    @property
    def user_repo(self) -> UserRepository:
        return self._user_repo

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def logger(self) -> Logger:
        return self._logger
