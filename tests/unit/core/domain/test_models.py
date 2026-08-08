from datetime import datetime, timezone
from uuid import UUID

import pytest

from aeoncord.core.domain.models import (
    Channel,
    ChannelId,
    Embed,
    Guild,
    GuildId,
    Mention,
    Message,
    MessageCreated,
    MessageDeleted,
    MessageEdited,
    MessageId,
    MessageType,
    ReactionAdded,
    ReactionRemoved,
    RoleId,
    Snowflake,
    User,
    UserId,
    UserOffline,
    UserOnline,
)


def make_user(
    user_id: UserId | None = None,
    *,
    username: str = "test-user",
    is_bot: bool = False,
    is_system: bool = False,
) -> User:
    return User(
        id=user_id or UserId(123),
        username=username,
        avatar_hash=None,
        is_bot=is_bot,
        is_system=is_system,
        locale="en-US",
        verified=True,
        email=None,
        mfa_enabled=False,
        premium_type=0,
        public_flags=0,
    )


def make_message(
    *,
    message_id: MessageId | None = None,
    channel_id: ChannelId | None = None,
    guild_id: GuildId | None = GuildId(456),
    author_id: UserId | None = None,
    content: str = "Hello, world!",
    embeds: list[Embed] | None = None,
    attachments: list[str] | None = None,
) -> Message:
    author_id = author_id or UserId(123)

    return Message(
        id=message_id or MessageId(789),
        channel_id=channel_id or ChannelId(456),
        guild_id=guild_id,
        author_id=author_id,
        author=make_user(author_id),
        content=content,
        created_at=datetime.now(timezone.utc),
        edited_at=None,
        is_pinned=False,
        is_tts=False,
        message_type=MessageType.DEFAULT,
        embeds=[] if embeds is None else embeds,
        attachments=[] if attachments is None else attachments,
    )


class TestValueObjects:
    def test_user_id_string_and_int_conversion(self) -> None:
        user_id = UserId(123456789)

        assert str(user_id) == "123456789"
        assert int(user_id) == 123456789

    def test_message_id_string_conversion(self) -> None:
        message_id = MessageId(123456789)

        assert str(message_id) == "123456789"

    def test_channel_id_string_conversion(self) -> None:
        channel_id = ChannelId(123456789)

        assert str(channel_id) == "123456789"

    def test_guild_id_string_conversion(self) -> None:
        guild_id = GuildId(123456789)

        assert str(guild_id) == "123456789"

    def test_role_id_string_conversion(self) -> None:
        role_id = RoleId(123456789)

        assert str(role_id) == "123456789"

    def test_value_objects_are_equal_by_value(self) -> None:
        assert UserId(123) == UserId(123)
        assert UserId(123) != UserId(456)

    def test_value_objects_are_immutable(self) -> None:
        user_id = UserId(123)

        with pytest.raises(AttributeError):
            user_id.value = 456  # type: ignore[misc]


class TestSnowflake:
    def test_to_timestamp_converts_discord_snowflake(self) -> None:
        snowflake = Snowflake(175928847299117063)

        result = snowflake.to_timestamp()

        assert result == datetime(2016, 4, 30, 11, 18, 25, 796000, tzinfo=timezone.utc)

    def test_discord_epoch_snowflake_maps_to_epoch(self) -> None:
        snowflake = Snowflake(0)

        result = snowflake.to_timestamp()

        assert result == datetime(2015, 1, 1, tzinfo=timezone.utc)


class TestMention:
    def test_empty_mention_is_invalid(self) -> None:
        mention = Mention()

        assert mention.is_valid() is False

    @pytest.mark.parametrize(
        "mention",
        [
            Mention(user_id=UserId(123)),
            Mention(role_id=RoleId(456)),
            Mention(channel_id=ChannelId(789)),
            Mention(guild_id=GuildId(101112)),
        ],
    )
    def test_mention_with_target_is_valid(self, mention: Mention) -> None:
        assert mention.is_valid() is True

    def test_mention_can_contain_multiple_targets(self) -> None:
        mention = Mention(
            user_id=UserId(123),
            role_id=RoleId(456),
            channel_id=ChannelId(789),
            guild_id=GuildId(101112),
        )

        assert mention.is_valid() is True


class TestEmbed:
    def test_empty_embed_is_invalid(self) -> None:
        embed = Embed()

        assert embed.is_valid() is False

    @pytest.mark.parametrize(
        "embed",
        [
            Embed(title="Title"),
            Embed(description="Description"),
        ],
    )
    def test_embed_with_title_or_description_is_valid(self, embed: Embed) -> None:
        assert embed.is_valid() is True

    def test_embed_with_only_metadata_is_invalid(self) -> None:
        embed = Embed(
            url="https://example.com",
            color=0xFFFFFF,
            image_url="https://example.com/image.png",
        )

        assert embed.is_valid() is False

    def test_embed_is_immutable(self) -> None:
        embed = Embed(title="Original")

        with pytest.raises(AttributeError):
            embed.title = "Changed"  # type: ignore[misc]


class TestUser:
    def test_display_name_returns_username(self) -> None:
        user = make_user(username="alice")

        assert user.display_name == "alice"

    @pytest.mark.parametrize(
        ("is_bot", "is_system", "expected"),
        [
            (False, False, False),
            (False, True, False),
            (True, False, False),
            (True, True, True),
        ],
    )
    def test_is_system_bot(
        self,
        is_bot: bool,
        is_system: bool,
        expected: bool,
    ) -> None:
        user = make_user(is_bot=is_bot, is_system=is_system)

        assert user.is_system_bot is expected


class TestMessage:
    def test_message_is_not_deleted_initially(self) -> None:
        message = make_message()

        assert message.is_deleted() is False

    def test_author_can_delete_message(self) -> None:
        author_id = UserId(123)
        message = make_message(author_id=author_id)

        assert message.can_delete(author_id) is True

    def test_non_author_cannot_delete_message(self) -> None:
        message = make_message(author_id=UserId(123))

        assert message.can_delete(UserId(456)) is False

    def test_admin_can_delete_message(self) -> None:
        message = make_message(author_id=UserId(123))

        assert message.can_delete(UserId(456), is_admin=True) is True

    def test_deleted_message_cannot_be_deleted(self) -> None:
        author_id = UserId(123)
        message = make_message(author_id=author_id)

        message.mark_deleted()

        assert message.can_delete(author_id) is False

    def test_author_can_edit_message(self) -> None:
        author_id = UserId(123)
        message = make_message(author_id=author_id)

        assert message.can_edit(author_id) is True

    def test_non_author_cannot_edit_message(self) -> None:
        message = make_message(author_id=UserId(123))

        assert message.can_edit(UserId(456)) is False

    def test_deleted_message_cannot_be_edited(self) -> None:
        author_id = UserId(123)
        message = make_message(author_id=author_id)

        message.mark_deleted()

        assert message.can_edit(author_id) is False

    def test_deleted_message_cannot_react(self) -> None:
        message = make_message()

        assert message.can_react() is True

        message.mark_deleted()

        assert message.can_react() is False

    def test_mark_deleted_changes_state(self) -> None:
        message = make_message()

        message.mark_deleted()

        assert message.is_deleted() is True

    def test_add_mention_adds_user(self) -> None:
        message = make_message()

        message.add_mention(UserId(456))

        assert message.mentions == [UserId(456)]

    def test_add_mention_does_not_duplicate_user(self) -> None:
        message = make_message()

        message.add_mention(UserId(456))
        message.add_mention(UserId(456))

        assert message.mentions == [UserId(456)]

    def test_add_reaction_creates_reaction(self) -> None:
        message = make_message()

        message.add_reaction("👍")

        assert message.reactions == {"👍": 1}

    def test_add_reaction_increments_count(self) -> None:
        message = make_message()

        message.add_reaction("👍")
        message.add_reaction("👍")

        assert message.reactions == {"👍": 2}

    def test_different_reactions_have_independent_counts(self) -> None:
        message = make_message()

        message.add_reaction("👍")
        message.add_reaction("❤️")
        message.add_reaction("👍")

        assert message.reactions == {
            "👍": 2,
            "❤️": 1,
        }

    def test_remove_reaction_decrements_count(self) -> None:
        message = make_message()

        message.add_reaction("👍")
        message.add_reaction("👍")

        message.remove_reaction("👍")

        assert message.reactions == {"👍": 1}

    def test_remove_last_reaction_deletes_entry(self) -> None:
        message = make_message()

        message.add_reaction("👍")
        message.remove_reaction("👍")

        assert message.reactions == {}

    def test_remove_unknown_reaction_does_nothing(self) -> None:
        message = make_message()

        message.remove_reaction("👍")

        assert message.reactions == {}

    def test_content_length_returns_character_count(self) -> None:
        message = make_message(content="Hello!")

        assert message.content_length() == 6

    def test_empty_message_with_whitespace_is_empty(self) -> None:
        message = make_message(content="   ")

        assert message.is_empty() is True

    def test_message_with_content_is_not_empty(self) -> None:
        message = make_message(content="Hello")

        assert message.is_empty() is False

    def test_message_with_embed_is_not_empty(self) -> None:
        message = make_message(
            content="",
            embeds=[Embed(title="Hello")],
        )

        assert message.is_empty() is False

    def test_message_with_attachment_is_not_empty(self) -> None:
        message = make_message(
            content="",
            attachments=["attachment-id"],
        )

        assert message.is_empty() is False

    def test_default_mutable_fields_are_independent(self) -> None:
        first = make_message()
        second = make_message()

        first.add_mention(UserId(456))
        first.add_reaction("👍")

        assert second.mentions == []
        assert second.reactions == {}


class TestChannel:
    def test_channel_with_no_guild_is_dm(self) -> None:
        channel = Channel(
            id=ChannelId(123),
            guild_id=None,
            name="DM",
            position=0,
            topic=None,
            is_nsfw=False,
            is_private=True,
            owner_id=UserId(456),
            created_at=datetime.now(timezone.utc),
        )

        assert channel.is_dm() is True

    def test_channel_with_guild_is_not_dm(self) -> None:
        channel = Channel(
            id=ChannelId(123),
            guild_id=GuildId(456),
            name="general",
            position=0,
            topic=None,
            is_nsfw=False,
            is_private=False,
            owner_id=None,
            created_at=datetime.now(timezone.utc),
        )

        assert channel.is_dm() is False


class TestGuild:
    def test_get_member_count_returns_member_count(self) -> None:
        guild = Guild(
            id=GuildId(123),
            name="Test Guild",
            icon_hash=None,
            owner_id=UserId(456),
            region="eu",
            member_count=42,
            created_at=datetime.now(timezone.utc),
        )

        assert guild.get_member_count() == 42


class TestDomainEvents:
    def test_message_created_generates_event_id_and_timestamp(self) -> None:
        event = MessageCreated(
            message_id=MessageId(123),
            author_id=UserId(456),
            channel_id=ChannelId(789),
        )

        assert isinstance(event.event_id, UUID)
        assert event.occurred_at.tzinfo == timezone.utc

    def test_domain_event_is_immutable(self) -> None:
        event = MessageCreated(
            message_id=MessageId(123),
            author_id=UserId(456),
            channel_id=ChannelId(789),
        )

        with pytest.raises(AttributeError):
            event.content = "Changed"  # type: ignore[misc]

    def test_message_created_defaults(self) -> None:
        event = MessageCreated(
            message_id=MessageId(123),
            author_id=UserId(456),
            channel_id=ChannelId(789),
        )

        assert event.guild_id is None
        assert event.content == ""

    def test_message_created_preserves_values(self) -> None:
        event = MessageCreated(
            message_id=MessageId(123),
            author_id=UserId(456),
            channel_id=ChannelId(789),
            guild_id=GuildId(111),
            content="Hello",
        )

        assert event.message_id == MessageId(123)
        assert event.author_id == UserId(456)
        assert event.channel_id == ChannelId(789)
        assert event.guild_id == GuildId(111)
        assert event.content == "Hello"

    def test_message_edited_preserves_values(self) -> None:
        edited_at = datetime.now(timezone.utc)

        event = MessageEdited(
            message_id=MessageId(123),
            editor_id=UserId(456),
            edited_at=edited_at,
            new_content="Updated",
        )

        assert event.message_id == MessageId(123)
        assert event.editor_id == UserId(456)
        assert event.edited_at == edited_at
        assert event.new_content == "Updated"

    def test_message_deleted_defaults(self) -> None:
        event = MessageDeleted(
            message_id=MessageId(123),
            channel_id=ChannelId(456),
        )

        assert event.deleter_id is None

    def test_reaction_added_defaults(self) -> None:
        event = ReactionAdded(
            message_id=MessageId(123),
            user_id=UserId(456),
        )

        assert event.emoji == ""

    def test_reaction_removed_defaults(self) -> None:
        event = ReactionRemoved(
            message_id=MessageId(123),
            user_id=UserId(456),
        )

        assert event.emoji == ""

    def test_user_online_preserves_values(self) -> None:
        timestamp = datetime.now(timezone.utc)

        event = UserOnline(
            user_id=UserId(123),
            timestamp=timestamp,
        )

        assert event.user_id == UserId(123)
        assert event.timestamp == timestamp

    def test_user_offline_preserves_values(self) -> None:
        timestamp = datetime.now(timezone.utc)

        event = UserOffline(
            user_id=UserId(123),
            timestamp=timestamp,
        )

        assert event.user_id == UserId(123)
        assert event.timestamp == timestamp
