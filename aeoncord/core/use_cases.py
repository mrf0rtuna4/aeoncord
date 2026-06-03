"""
Application Use Cases (Interactors).

Orchestrate domain models and coordinate with ports.
These are application services that implement specific business processes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from aeoncord.core.domain.exceptions import (
    EmptyMessageError,
    InvalidMessageContentError,
    InvalidMessageLengthError,
    MessageAlreadyDeletedError,
    MessageNotFoundError,
    NotMessageAuthorError,
)
from aeoncord.core.domain.models import (
    ChannelId,
    GuildId,
    Message,
    MessageCreated,
    MessageDeleted,
    MessageEdited,
    MessageId,
    ReactionAdded,
    ReactionRemoved,
    UserId,
)
from aeoncord.core.ports import EventBus, Logger, MessageRepository


class SendMessageUseCase:
    """
    Use Case: Send a message to a channel.

    Business rules:
    - Content must not be empty
    - Content must not exceed 2000 characters
    - At least text OR embed OR attachment required
    """

    def __init__(
        self,
        message_repo: MessageRepository,
        event_bus: EventBus,
        logger: Logger,
    ):
        self.message_repo = message_repo
        self.event_bus = event_bus
        self.logger = logger

    async def execute(
        self,
        channel_id: ChannelId,
        author_id: UserId,
        content: str,
        guild_id: Optional[GuildId] = None,
    ) -> Message:
        """
        Send a message.

        Args:
            channel_id: Target channel
            author_id: Message author
            content: Message text content
            guild_id: Guild context (if applicable)

        Returns:
            Created message aggregate

        Raises:
            InvalidMessageContentError: Content validation failed
            EmptyMessageError: Message has no content
        """
        if not isinstance(content, str):
            raise InvalidMessageContentError("Content must be a string", {"content": content})

        if len(content) > 2000:
            raise InvalidMessageLengthError(
                f"Content exceeds 2000 character limit ({len(content)})", {"length": len(content)}
            )

        if not content.strip():
            raise EmptyMessageError("Message content cannot be empty", {"content": content})

        message = Message(
            id=MessageId(0),
            channel_id=channel_id,
            guild_id=guild_id,
            author_id=author_id,
            author=None,
            content=content,
            created_at=datetime.now(),
            edited_at=None,
            is_pinned=False,
            is_tts=False,
            message_type="default",
        )

        await self.message_repo.save(message)

        self.logger.info(
            f"Message sent to channel {channel_id}",
            message_id=message.id,
            author_id=author_id,
        )

        await self.event_bus.publish(
            MessageCreated(
                message_id=message.id,
                author_id=author_id,
                channel_id=channel_id,
                guild_id=guild_id,
                content=content,
            )
        )

        return message


class EditMessageUseCase:
    """Use Case: Edit an existing message."""

    def __init__(
        self,
        message_repo: MessageRepository,
        event_bus: EventBus,
        logger: Logger,
    ):
        self.message_repo = message_repo
        self.event_bus = event_bus
        self.logger = logger

    async def execute(
        self,
        message_id: MessageId,
        editor_id: UserId,
        new_content: str,
    ) -> Message:
        """
        Edit a message.

        Return:
            Message | None

        Raises:
            MessageNotFound: Message doesn't exist
            NotMessageAuthor: Requester is not author
            MessageAlreadyDeleted: Cannot edit deleted message
            InvalidMessageContentError: Content validation failed
        """
        message = await self.message_repo.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(
                f"Message {message_id} not found", {"message_id": str(message_id)}
            )

        if not message.can_edit(editor_id):
            raise NotMessageAuthorError(
                f"User {editor_id} cannot edit this message",
                {"message_id": str(message_id), "editor_id": str(editor_id)},
            )

        if not isinstance(new_content, str) or not new_content.strip():
            raise InvalidMessageContentError("New content must be non-empty string")

        if len(new_content) > 2000:
            raise InvalidMessageLengthError("Content exceeds 2000 characters")

        old_content = message.content
        message.content = new_content
        message.edited_at = datetime.now()

        await self.message_repo.save(message)

        self.logger.info(
            f"Message {message_id} edited",
            editor_id=editor_id,
            old_length=len(old_content),
            new_length=len(new_content),
        )

        await self.event_bus.publish(
            MessageEdited(
                message_id=message_id,
                editor_id=editor_id,
                new_content=new_content,
                edited_at=message.edited_at,
            )
        )

        return message


class DeleteMessageUseCase:
    """Use Case: Delete a message."""

    def __init__(
        self,
        message_repo: MessageRepository,
        event_bus: EventBus,
        logger: Logger,
    ):
        self.message_repo = message_repo
        self.event_bus = event_bus
        self.logger = logger

    async def execute(
        self,
        message_id: MessageId,
        requester_id: UserId,
        is_admin: bool = False,
    ) -> None:
        """
        Delete a message.

        Raises:
            MessageNotFound: Message doesn't exist
            PermissionDenied: Requester lacks permission
            MessageAlreadyDeleted: Message is already deleted
        """
        message = await self.message_repo.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(
                f"Message {message_id} not found", {"message_id": str(message_id)}
            )

        if message.is_deleted():
            raise MessageAlreadyDeletedError(
                f"Message {message_id} is already deleted", {"message_id": str(message_id)}
            )

        if not message.can_delete(requester_id, is_admin=is_admin):
            raise NotMessageAuthorError(
                f"User {requester_id} cannot delete this message",
                {"message_id": str(message_id), "requester_id": str(requester_id)},
            )

        message.mark_deleted()
        await self.message_repo.save(message)
        await self.message_repo.delete(message_id)

        self.logger.info(
            f"Message {message_id} deleted",
            deleter_id=requester_id,
        )

        await self.event_bus.publish(
            MessageDeleted(
                message_id=message_id,
                channel_id=message.channel_id,
                deleter_id=requester_id,
            )
        )


class AddReactionUseCase:
    """Use Case: Add reaction to message."""

    def __init__(
        self,
        message_repo: MessageRepository,
        event_bus: EventBus,
        logger: Logger,
    ):
        self.message_repo = message_repo
        self.event_bus = event_bus
        self.logger = logger

    async def execute(
        self,
        message_id: MessageId,
        user_id: UserId,
        emoji: str,
    ) -> None:
        """
        Add reaction to a message.

        Raises:
            MessageNotFound: Message doesn't exist
            MessageAlreadyDeleted: Cannot react to deleted message
        """
        message = await self.message_repo.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(f"Message {message_id} not found")

        if not message.can_react():
            raise MessageAlreadyDeletedError("Cannot react to deleted message")

        message.add_reaction(emoji)
        await self.message_repo.save(message)

        self.logger.debug(
            f"Reaction added to message {message_id}",
            emoji=emoji,
            user_id=str(user_id),
        )

        await self.event_bus.publish(
            ReactionAdded(
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )
        )


class RemoveReactionUseCase:
    """Use Case: Remove reaction from message."""

    def __init__(
        self,
        message_repo: MessageRepository,
        event_bus: EventBus,
        logger: Logger,
    ):
        self.message_repo = message_repo
        self.event_bus = event_bus
        self.logger = logger

    async def execute(
        self,
        message_id: MessageId,
        user_id: UserId,
        emoji: str,
    ) -> None:
        """Remove reaction from message."""
        message = await self.message_repo.get_by_id(message_id)
        if not message:
            raise MessageNotFoundError(f"Message {message_id} not found")

        message.remove_reaction(emoji)
        await self.message_repo.save(message)

        self.logger.debug(
            f"Reaction removed from message {message_id}",
            emoji=emoji,
            user_id=str(user_id),
        )

        await self.event_bus.publish(
            ReactionRemoved(
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )
        )
