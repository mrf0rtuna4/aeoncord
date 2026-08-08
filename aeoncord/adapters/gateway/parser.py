"""
Discord Gateway payload parser.

Converts raw JSON dictionaries into validated Gateway models.
"""

from __future__ import annotations

from typing import cast

from aeoncord.adapters.gateway.models import (
    GatewayMessageCreate,
    GatewayMessageDelete,
    GatewayMessageUpdate,
    GatewayPresenceUpdate,
    GatewayReaction,
)

from aeoncord.adapters.gateway.payloads import (
    MessageCreatePayload,
    MessageDeletePayload,
    MessageUpdatePayload,
    PresenceUpdatePayload,
    ReactionAddPayload,
    ReactionRemovePayload,
)


class GatewayParser:
    """
    Parses Discord Gateway JSON payloads.
    """

    def parse_message_create(
        self,
        data: dict[str, object],
    ) -> GatewayMessageCreate:

        payload = cast(MessageCreatePayload, data)

        author = payload["author"]

        return GatewayMessageCreate(
            id=payload["id"],
            channel_id=payload["channel_id"],
            guild_id=payload.get("guild_id"),
            author_id=author["id"],
            content=payload.get("content", ""),
        )


    def parse_message_update(
        self,
        data: dict[str, object],
    ) -> GatewayMessageUpdate:

        payload = cast(MessageUpdatePayload, data)

        author = payload.get("author")

        return GatewayMessageUpdate(
            id=payload["id"],
            channel_id=payload.get("channel_id"),
            guild_id=payload.get("guild_id"),
            author_id=author["id"] if author else None,
            content=payload.get("content"),
            edited_timestamp=payload.get("edited_timestamp"),
        )


    def parse_message_delete(
        self,
        data: dict[str, object],
    ) -> GatewayMessageDelete:

        payload = cast(MessageDeletePayload, data)

        return GatewayMessageDelete(
            id=payload["id"],
            channel_id=payload["channel_id"],
            guild_id=payload.get("guild_id"),
        )


    def parse_reaction_add(
        self,
        data: dict[str, object],
    ) -> GatewayReaction:

        payload = cast(ReactionAddPayload, data)

        return GatewayReaction(
            message_id=payload["message_id"],
            user_id=payload["user_id"],
            emoji=payload["emoji"]["name"],
        )


    def parse_reaction_remove(
        self,
        data: dict[str, object],
    ) -> GatewayReaction:

        payload = cast(ReactionRemovePayload, data)

        return GatewayReaction(
            message_id=payload["message_id"],
            user_id=payload["user_id"],
            emoji=payload["emoji"]["name"],
        )


    def parse_presence_update(
        self,
        data: dict[str, object],
    ) -> GatewayPresenceUpdate:

        payload = cast(PresenceUpdatePayload, data)

        user = payload["user"]

        return GatewayPresenceUpdate(
            user_id=user["id"],
            status=payload.get("status", "offline"),
        )
    