"""
Gateway dataclass -> DomainEvent mapper.
"""

from __future__ import annotations

from datetime import datetime

from aeoncord.core.domain.models import (
    ChannelId,
    DomainEvent,
    GuildId,
    MessageCreated,
    MessageDeleted,
    MessageEdited,
    MessageId,
    ReactionAdded,
    ReactionRemoved,
    UserId,
    UserOffline,
    UserOnline,
)
from aeoncord.adapters.gateway.models import (
    GatewayMessageCreate,
    GatewayMessageDelete,
    GatewayMessageUpdate,
    GatewayPresenceUpdate,
    GatewayReaction,
)


class GatewayMapper:
    """
    Converts validated Gateway models into domain events.
    """

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def map_message_create(self, payload: GatewayMessageCreate) -> MessageCreated:
        return MessageCreated(
            message_id=MessageId(int(payload.id)),
            author_id=UserId(int(payload.author_id)),
            channel_id=ChannelId(int(payload.channel_id)),
            guild_id=GuildId(int(payload.guild_id)) if payload.guild_id is not None else None,
            content=payload.content,
        )

    def map_message_update(self, payload: GatewayMessageUpdate) -> MessageEdited:
        if payload.edited_timestamp is None:
            raise ValueError("MESSAGE_UPDATE payload is missing edited_timestamp")

        return MessageEdited(
            message_id=MessageId(int(payload.id)),
            editor_id=UserId(int(payload.author_id)) if payload.author_id is not None else UserId(0),
            new_content=payload.content or "",
            edited_at=self._parse_timestamp(payload.edited_timestamp),
        )

    def map_message_delete(self, payload: GatewayMessageDelete) -> MessageDeleted:
        return MessageDeleted(
            message_id=MessageId(int(payload.id)),
            channel_id=ChannelId(int(payload.channel_id)),
            deleter_id=None,
        )

    def map_reaction_added(self, payload: GatewayReaction) -> ReactionAdded:
        return ReactionAdded(
            message_id=MessageId(int(payload.message_id)),
            user_id=UserId(int(payload.user_id)),
            emoji=payload.emoji,
        )

    def map_reaction_removed(self, payload: GatewayReaction) -> ReactionRemoved:
        return ReactionRemoved(
            message_id=MessageId(int(payload.message_id)),
            user_id=UserId(int(payload.user_id)),
            emoji=payload.emoji,
        )

    def map_presence_update(self, payload: GatewayPresenceUpdate) -> DomainEvent:
        user_id = UserId(int(payload.user_id))

        if payload.status == "offline":
            return UserOffline(
                user_id=user_id,
                timestamp=datetime.now(),
            )

        return UserOnline(
            user_id=user_id,
            timestamp=datetime.now(),
        )
    