import pytest

from aeoncord.core.domain.exceptions import (
    AlreadyConnectedError,
    AlreadyLoadedError,
    AuthenticationFailedError,
    ChannelNotFoundError,
    DomainError,
    EmptyMessageError,
    EntityNotFoundError,
    GuildNotFoundError,
    InsufficientRoleError,
    InvalidChannelIdError,
    InvalidGuildIdError,
    InvalidMentionFormatError,
    InvalidMessageContentError,
    InvalidMessageLengthError,
    InvalidOperationError,
    InvalidSnowflakeError,
    InvalidStateError,
    InvalidTokenError,
    InvalidUserIdError,
    MessageAlreadyDeletedError,
    MessageNotFoundError,
    MessageTooOldError,
    NotChannelOwnerError,
    NotConnectedError,
    NotGuildOwnerError,
    NotMessageAuthorError,
    PermissionDeniedError,
    RateLimitedError,
    RoleNotFoundError,
    TokenExpiredError,
    UserNotFoundError,
)


class TestDomainError:
    def test_stores_message(self) -> None:
        error = DomainError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"

    def test_context_defaults_to_empty_dict(self) -> None:
        error = DomainError("Something went wrong")

        assert error.context == {}

    def test_stores_context(self) -> None:
        context = {
            "message_id": 123,
            "operation": "delete",
        }

        error = DomainError("Something went wrong", context)

        assert error.context == context

    def test_context_is_not_shared_between_instances(self) -> None:
        first = DomainError("First")
        second = DomainError("Second")

        first.context["key"] = "value"

        assert second.context == {}


class TestExceptionHierarchy:
    @pytest.mark.parametrize(
        ("exception", "parent"),
        [
            (PermissionDeniedError, DomainError),
            (NotMessageAuthorError, PermissionDeniedError),
            (NotChannelOwnerError, PermissionDeniedError),
            (NotGuildOwnerError, PermissionDeniedError),
            (InsufficientRoleError, PermissionDeniedError),
            (EntityNotFoundError, DomainError),
            (MessageNotFoundError, EntityNotFoundError),
            (UserNotFoundError, EntityNotFoundError),
            (ChannelNotFoundError, EntityNotFoundError),
            (GuildNotFoundError, EntityNotFoundError),
            (RoleNotFoundError, EntityNotFoundError),
            (InvalidOperationError, DomainError),
            (MessageAlreadyDeletedError, InvalidOperationError),
            (InvalidMessageContentError, InvalidOperationError),
            (InvalidMessageLengthError, InvalidMessageContentError),
            (EmptyMessageError, InvalidMessageContentError),
            (MessageTooOldError, InvalidOperationError),
            (RateLimitedError, InvalidOperationError),
            (InvalidMentionFormatError, InvalidOperationError),
            (AuthenticationFailedError, DomainError),
            (InvalidTokenError, AuthenticationFailedError),
            (TokenExpiredError, AuthenticationFailedError),
            (InvalidStateError, DomainError),
            (AlreadyConnectedError, InvalidStateError),
            (NotConnectedError, InvalidStateError),
            (AlreadyLoadedError, InvalidStateError),
            (InvalidSnowflakeError, DomainError),
            (InvalidUserIdError, DomainError),
            (InvalidChannelIdError, DomainError),
            (InvalidGuildIdError, DomainError),
        ],
    )
    def test_exception_inherits_from_expected_parent(
        self,
        exception: type[Exception],
        parent: type[Exception],
    ) -> None:
        assert issubclass(exception, parent)


class TestInvalidMessageContentError:
    def test_default_message(self) -> None:
        error = InvalidMessageContentError()

        assert str(error) == "Invalid message content: Content is invalid"
        assert error.message == "Invalid message content: Content is invalid"

    def test_custom_reason(self) -> None:
        error = InvalidMessageContentError("too long")

        assert str(error) == "Invalid message content: too long"

    def test_preserves_context(self) -> None:
        context = {"message_id": 123}

        error = InvalidMessageContentError("too long", context)

        assert error.context == context

    def test_specialized_errors_are_invalid_message_content_errors(self) -> None:
        assert issubclass(InvalidMessageLengthError, InvalidMessageContentError)
        assert issubclass(EmptyMessageError, InvalidMessageContentError)
