"""
Domain-specific exceptions.

They are raised in the core domain layer and caught by adapters/handlers.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    def __init__(self, message: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class PermissionDeniedError(DomainError):
    """User lacks permission to perform action."""

    pass


class NotMessageAuthorError(PermissionDeniedError):
    """Only the message author can perform this action."""

    pass


class NotChannelOwnerError(PermissionDeniedError):
    """Only the channel owner can perform this action."""

    pass


class NotGuildOwnerError(PermissionDeniedError):
    """Only the guild owner can perform this action."""

    pass


class InsufficientRoleError(PermissionDeniedError):
    """User's roles don't grant required permissions."""

    pass


class EntityNotFoundError(DomainError):
    """Requested entity does not exist."""

    pass


class MessageNotFoundError(EntityNotFoundError):
    """Message with given ID not found."""

    pass


class UserNotFoundError(EntityNotFoundError):
    """User with given ID not found."""

    pass


class ChannelNotFoundError(EntityNotFoundError):
    """Channel with given ID not found."""

    pass


class GuildNotFoundError(EntityNotFoundError):
    """Guild with given ID not found."""

    pass


class RoleNotFoundError(EntityNotFoundError):
    """Role with given ID not found."""

    pass


class InvalidOperationError(DomainError):
    """Operation violates a business rule."""

    pass


class MessageAlreadyDeletedError(InvalidOperationError):
    """Cannot perform action on deleted message."""

    pass


class InvalidMessageContentError(InvalidOperationError):
    """Message content violates validation rules."""

    def __init__(self, reason: str = "Content is invalid", context: dict[str, Any] | None = None):
        super().__init__(f"Invalid message content: {reason}", context)


class InvalidMessageLengthError(InvalidMessageContentError):
    """Message content exceeds length limits."""

    pass


class EmptyMessageError(InvalidMessageContentError):
    """Message has no content, embeds, or attachments."""

    pass


class MessageTooOldError(InvalidOperationError):
    """Cannot edit or delete message older than 2 weeks."""

    pass


class RateLimitedError(InvalidOperationError):
    """Operation rate limited by Discord."""

    pass


class InvalidMentionFormatError(InvalidOperationError):
    """Mention format is invalid."""

    pass


class AuthenticationFailedError(DomainError):
    """Authentication failed."""

    pass


class InvalidTokenError(AuthenticationFailedError):
    """Provided token is invalid or expired."""

    pass


class TokenExpiredError(AuthenticationFailedError):
    """Authentication token has expired."""

    pass


class InvalidStateError(DomainError):
    """Operation invalid for current state."""

    pass


class AlreadyConnectedError(InvalidStateError):
    """Client is already connected."""

    pass


class NotConnectedError(InvalidStateError):
    """Client is not connected."""

    pass


class AlreadyLoadedError(InvalidStateError):
    """Resource is already loaded."""

    pass


class InvalidValueObjectError(DomainError):
    """Value object failed validation."""

    pass


class InvalidSnowflakeError(InvalidValueObjectError):
    pass


class InvalidUserIdError(InvalidValueObjectError):
    pass


class InvalidChannelIdError(InvalidValueObjectError):
    pass


class InvalidGuildIdError(InvalidValueObjectError):
    pass
