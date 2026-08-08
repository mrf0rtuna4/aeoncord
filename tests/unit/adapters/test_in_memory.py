from datetime import datetime, timezone

import pytest

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
    Channel,
    ChannelId,
    Guild,
    GuildId,
    Message,
    MessageCreated,
    MessageId,
    MessageType,
    Role,
    RoleId,
    User,
    UserId,
)


def make_user(user_id: int = 1) -> User:
    return User(
        id=UserId(user_id),
        username=f"user-{user_id}",
        avatar_hash=None,
        is_bot=False,
        is_system=False,
        locale="en-US",
        verified=True,
        email=None,
        mfa_enabled=False,
        premium_type=0,
        public_flags=0,
    )


def make_message(
    message_id: int = 1,
    channel_id: int = 10,
    *,
    content: str = "hello",
    created_at: datetime | None = None,
) -> Message:
    user_id = UserId(100)

    return Message(
        id=MessageId(message_id),
        channel_id=ChannelId(channel_id),
        guild_id=GuildId(20),
        author_id=user_id,
        author=make_user(100),
        content=content,
        created_at=created_at or datetime.now(timezone.utc),
        edited_at=None,
        is_pinned=False,
        is_tts=False,
        message_type=MessageType.DEFAULT,
    )


def make_channel(
    channel_id: int = 1,
    guild_id: int = 10,
) -> Channel:
    return Channel(
        id=ChannelId(channel_id),
        guild_id=GuildId(guild_id),
        name=f"channel-{channel_id}",
        position=0,
        topic=None,
        is_nsfw=False,
        is_private=False,
        owner_id=None,
        created_at=datetime.now(timezone.utc),
    )


def make_guild(guild_id: int = 1) -> Guild:
    return Guild(
        id=GuildId(guild_id),
        name=f"guild-{guild_id}",
        icon_hash=None,
        owner_id=UserId(100),
        region="eu",
        member_count=10,
        created_at=datetime.now(timezone.utc),
    )


def make_role(
    role_id: int = 1,
    guild_id: int = 10,
) -> Role:
    return Role(
        id=RoleId(role_id),
        guild_id=GuildId(guild_id),
        name=f"role-{role_id}",
        color=0,
        position=0,
        permissions=0,
        is_hoisted=False,
        is_managed=False,
        is_mentionable=False,
    )


class TestInMemoryMessageRepository:
    @pytest.mark.asyncio
    async def test_get_missing_message_returns_none(self) -> None:
        repository = InMemoryMessageRepository()

        result = await repository.get_by_id(MessageId(999))

        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get_message(self) -> None:
        repository = InMemoryMessageRepository()
        message = make_message()

        await repository.save(message)

        assert await repository.get_by_id(message.id) is message

    @pytest.mark.asyncio
    async def test_save_replaces_existing_message(self) -> None:
        repository = InMemoryMessageRepository()
        first = make_message(content="first")
        second = make_message(content="second")

        await repository.save(first)
        await repository.save(second)

        result = await repository.get_by_id(first.id)

        assert result is second

    @pytest.mark.asyncio
    async def test_get_many_returns_messages_for_channel(self) -> None:
        repository = InMemoryMessageRepository()

        first = make_message(
            message_id=1,
            channel_id=10,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        second = make_message(
            message_id=2,
            channel_id=10,
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        other_channel = make_message(
            message_id=3,
            channel_id=20,
            created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
        )

        await repository.save(first)
        await repository.save(second)
        await repository.save(other_channel)

        result = await repository.get_many_by_channel(ChannelId(10))

        assert result == [second, first]

    @pytest.mark.asyncio
    async def test_get_many_respects_limit(self) -> None:
        repository = InMemoryMessageRepository()

        for message_id in range(1, 6):
            await repository.save(
                make_message(message_id=message_id, channel_id=10),
            )

        result = await repository.get_many_by_channel(
            ChannelId(10),
            limit=2,
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_many_excludes_deleted_messages(self) -> None:
        repository = InMemoryMessageRepository()

        active = make_message(message_id=1, channel_id=10)
        deleted = make_message(message_id=2, channel_id=10)
        deleted.mark_deleted()

        await repository.save(active)
        await repository.save(deleted)

        result = await repository.get_many_by_channel(ChannelId(10))

        assert result == [active]

    @pytest.mark.asyncio
    async def test_delete_existing_message(self) -> None:
        repository = InMemoryMessageRepository()
        message = make_message()

        await repository.save(message)
        await repository.delete(message.id)

        assert await repository.get_by_id(message.id) is None

    @pytest.mark.asyncio
    async def test_delete_missing_message_does_nothing(self) -> None:
        repository = InMemoryMessageRepository()

        await repository.delete(MessageId(999))

        assert await repository.get_by_id(MessageId(999)) is None

    @pytest.mark.asyncio
    async def test_clear_removes_all_messages(self) -> None:
        repository = InMemoryMessageRepository()

        await repository.save(make_message(message_id=1))
        await repository.save(make_message(message_id=2))

        repository.clear()

        assert await repository.get_by_id(MessageId(1)) is None
        assert await repository.get_by_id(MessageId(2)) is None


class TestInMemoryUserRepository:
    @pytest.mark.asyncio
    async def test_get_missing_user_returns_none(self) -> None:
        repository = InMemoryUserRepository()

        assert await repository.get_by_id(UserId(999)) is None

    @pytest.mark.asyncio
    async def test_save_and_get_user(self) -> None:
        repository = InMemoryUserRepository()
        user = make_user()

        await repository.save(user)

        assert await repository.get_by_id(user.id) is user

    @pytest.mark.asyncio
    async def test_get_current_user_without_user_raises(self) -> None:
        repository = InMemoryUserRepository()

        with pytest.raises(ValueError, match="Current user not set"):
            await repository.get_current_user()

    @pytest.mark.asyncio
    async def test_set_and_get_current_user(self) -> None:
        repository = InMemoryUserRepository()
        user = make_user()

        repository.set_current_user(user)

        assert await repository.get_current_user() is user


class TestInMemoryChannelRepository:
    @pytest.mark.asyncio
    async def test_get_missing_channel_returns_none(self) -> None:
        repository = InMemoryChannelRepository()

        assert await repository.get_by_id(ChannelId(999)) is None

    @pytest.mark.asyncio
    async def test_save_and_get_channel(self) -> None:
        repository = InMemoryChannelRepository()
        channel = make_channel()

        await repository.save(channel)

        assert await repository.get_by_id(channel.id) is channel

    @pytest.mark.asyncio
    async def test_get_many_by_guild_filters_channels(self) -> None:
        repository = InMemoryChannelRepository()

        first = make_channel(channel_id=1, guild_id=10)
        second = make_channel(channel_id=2, guild_id=10)
        other = make_channel(channel_id=3, guild_id=20)

        await repository.save(first)
        await repository.save(second)
        await repository.save(other)

        result = await repository.get_many_by_guild(GuildId(10))

        assert result == [first, second]


class TestInMemoryGuildRepository:
    @pytest.mark.asyncio
    async def test_get_missing_guild_returns_none(self) -> None:
        repository = InMemoryGuildRepository()

        assert await repository.get_by_id(GuildId(999)) is None

    @pytest.mark.asyncio
    async def test_save_and_get_guild(self) -> None:
        repository = InMemoryGuildRepository()
        guild = make_guild()

        await repository.save(guild)

        assert await repository.get_by_id(guild.id) is guild

    @pytest.mark.asyncio
    async def test_get_user_guilds_returns_stored_guilds(self) -> None:
        repository = InMemoryGuildRepository()

        first = make_guild(1)
        second = make_guild(2)

        await repository.save(first)
        await repository.save(second)

        result = await repository.get_user_guilds(UserId(100))

        assert result == [first, second]


class TestInMemoryRoleRepository:
    @pytest.mark.asyncio
    async def test_get_missing_role_returns_none(self) -> None:
        repository = InMemoryRoleRepository()

        assert await repository.get_by_id(RoleId(999)) is None

    @pytest.mark.asyncio
    async def test_save_and_get_role(self) -> None:
        repository = InMemoryRoleRepository()
        role = make_role()

        await repository.save(role)

        assert await repository.get_by_id(role.id) is role

    @pytest.mark.asyncio
    async def test_get_many_by_guild_filters_roles(self) -> None:
        repository = InMemoryRoleRepository()

        first = make_role(role_id=1, guild_id=10)
        second = make_role(role_id=2, guild_id=10)
        other = make_role(role_id=3, guild_id=20)

        await repository.save(first)
        await repository.save(second)
        await repository.save(other)

        result = await repository.get_many_by_guild(GuildId(10))

        assert result == [first, second]


class TestInMemoryEventBus:
    @pytest.mark.asyncio
    async def test_subscribed_handler_receives_event(self) -> None:
        event_bus = InMemoryEventBus()
        received: list[object] = []

        async def handler(event: MessageCreated) -> None:
            received.append(event)

        await event_bus.subscribe(MessageCreated, handler)

        event = MessageCreated(
            message_id=MessageId(1),
            author_id=UserId(2),
            channel_id=ChannelId(3),
        )

        await event_bus.publish(event)

        assert received == [event]

    @pytest.mark.asyncio
    async def test_multiple_handlers_receive_event(self) -> None:
        event_bus = InMemoryEventBus()
        received: list[object] = []

        async def first_handler(event: MessageCreated) -> None:
            received.append(("first", event))

        async def second_handler(event: MessageCreated) -> None:
            received.append(("second", event))

        await event_bus.subscribe(MessageCreated, first_handler)
        await event_bus.subscribe(MessageCreated, second_handler)

        event = MessageCreated(
            message_id=MessageId(1),
            author_id=UserId(2),
            channel_id=ChannelId(3),
        )

        await event_bus.publish(event)

        assert received == [
            ("first", event),
            ("second", event),
        ]

    @pytest.mark.asyncio
    async def test_unsubscribe_stops_handler_from_receiving_events(self) -> None:
        event_bus = InMemoryEventBus()
        received: list[object] = []

        async def handler(event: MessageCreated) -> None:
            received.append(event)

        await event_bus.subscribe(MessageCreated, handler)
        await event_bus.unsubscribe(MessageCreated, handler)

        await event_bus.publish(
            MessageCreated(
                message_id=MessageId(1),
                author_id=UserId(2),
                channel_id=ChannelId(3),
            )
        )

        assert received == []

    @pytest.mark.asyncio
    async def test_unsubscribe_unknown_event_type_does_nothing(self) -> None:
        event_bus = InMemoryEventBus()

        async def handler(event: MessageCreated) -> None:
            pass

        await event_bus.unsubscribe(MessageCreated, handler)

    @pytest.mark.asyncio
    async def test_handler_error_does_not_stop_publish(self) -> None:
        event_bus = InMemoryEventBus()
        received: list[object] = []

        async def failing_handler(event: MessageCreated) -> None:
            raise RuntimeError("boom")

        async def working_handler(event: MessageCreated) -> None:
            received.append(event)

        await event_bus.subscribe(MessageCreated, failing_handler)
        await event_bus.subscribe(MessageCreated, working_handler)

        await event_bus.publish(
            MessageCreated(
                message_id=MessageId(1),
                author_id=UserId(2),
                channel_id=ChannelId(3),
            )
        )

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_only_matching_event_type_is_published(self) -> None:
        event_bus = InMemoryEventBus()
        received: list[object] = []

        async def handler(event: MessageCreated) -> None:
            received.append(event)

        await event_bus.subscribe(MessageCreated, handler)

        await event_bus.publish(
            MessageCreated(
                message_id=MessageId(1),
                author_id=UserId(2),
                channel_id=ChannelId(3),
            )
        )

        assert len(received) == 1


class TestSimpleLogger:
    def test_debug_logs_message(self, caplog: pytest.LogCaptureFixture) -> None:
        logger = SimpleLogger("test-debug")

        with caplog.at_level("DEBUG", logger="test-debug"):
            logger.debug("debug message", request_id=123)

        assert "debug message" in caplog.text

    def test_info_logs_message(self, caplog: pytest.LogCaptureFixture) -> None:
        logger = SimpleLogger("test-info")

        with caplog.at_level("INFO", logger="test-info"):
            logger.info("info message", request_id=123)

        assert "info message" in caplog.text

    def test_warning_logs_message(self, caplog: pytest.LogCaptureFixture) -> None:
        logger = SimpleLogger("test-warning")

        with caplog.at_level("WARNING", logger="test-warning"):
            logger.warning("warning message", request_id=123)

        assert "warning message" in caplog.text

    def test_error_logs_message(self, caplog: pytest.LogCaptureFixture) -> None:
        logger = SimpleLogger("test-error")

        with caplog.at_level("ERROR", logger="test-error"):
            logger.error("error message", request_id=123)

        assert "error message" in caplog.text
