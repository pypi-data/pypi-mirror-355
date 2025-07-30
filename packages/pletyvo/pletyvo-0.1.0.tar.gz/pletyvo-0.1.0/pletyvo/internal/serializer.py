# Copyright (c) 2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = ("as_dict",)

import typing

from classes import typeclass

from pletyvo.dapp.event import (
    AuthHeader,
    EventInput,
    Event,
    EventResponse,
)
from pletyvo.delivery.channel import (
    Channel,
    ChannelCreateInput,
    ChannelUpdateInput,
)
from pletyvo.delivery.message import (
    Message,
    MessageInput,
)
from pletyvo.delivery.post import (
    Post,
    PostCreateInput,
    PostUpdateInput,
)

from typing import Any


@typeclass
def as_dict(  # type: ignore[empty-body]
    instance: AuthHeader
    | EventInput
    | Event
    | EventResponse
    | Channel
    | ChannelCreateInput
    | ChannelUpdateInput
    | Message
    | MessageInput
    | Post
    | PostCreateInput
    | PostUpdateInput,
) -> dict: ...


@as_dict.instance(AuthHeader)
def _as_dict_dapp_auth_header(instance: AuthHeader):
    from base64 import b64encode

    return {
        "sch": instance.sch,
        "pub": b64encode(instance.pub).decode(),
        "sig": b64encode(instance.sig).decode(),
    }


@as_dict.instance(EventInput)
def _as_dict_dapp_event_input(instance: EventInput):
    return {
        "body": str(instance.body),
        "auth": as_dict(instance.auth),  # type: ignore[arg-type]
    }


@as_dict.instance(Event)
def _as_dict_dapp_event(instance: Event):
    return {
        "id": str(instance.id),
        "body": str(instance.body),
        "auth": as_dict(instance.auth),  # type: ignore[arg-type]
    }


@as_dict.instance(EventResponse)
def _as_dict_dapp_event_response(instance: EventResponse):
    return {
        "id": str(instance.id),
    }


@as_dict.instance(Channel)
def _as_dict_delivery_channel(instance: Channel) -> dict[str, Any]:
    return {
        "id": str(instance.id),
        "hash": str(instance.hash),
        "author": str(instance.author),
        "name": str(instance.name),
    }


@as_dict.instance(ChannelCreateInput)
def _as_dict_delivery_channel_create_input(
    instance: ChannelCreateInput,
) -> dict[str, Any]:
    return {
        "name": instance.name,
    }


@as_dict.instance(ChannelUpdateInput)
def _as_dict_delivery_channel_update_input(
    instance: ChannelUpdateInput,
) -> dict[str, Any]:
    return {
        "name": instance.name,
    }


@as_dict.instance(Message)
def _as_dict_delivery_message(instance: Message) -> dict[str, Any]:
    return {
        "body": str(instance.body),
        "auth": as_dict(instance.auth),  # type: ignore[arg-type]
    }


@as_dict.instance(MessageInput)
def _as_dict_delivery_message_input(instance: MessageInput) -> dict[str, Any]:
    return {
        "id": str(instance.id),
        "channel": str(instance.channel),
        "content": instance.content,
    }


@as_dict.instance(Post)
def _as_dict_delivery_post(instance: Post) -> dict[str, Any]:
    return {
        "id": str(instance.id),
        "hash": str(instance.hash),
        "author": str(instance.author),
        "channel": str(instance.channel),
        "content": instance.content,
    }


@as_dict.instance(PostCreateInput)
def _as_dict_delivery_post_create_input(
    instance: PostCreateInput,
) -> dict[str, Any]:
    return {
        "channel": str(instance.channel),
        "content": instance.content,
    }


@as_dict.instance(PostUpdateInput)
def _as_dict_delivery_post_update_input(
    instance: PostUpdateInput,
) -> dict[str, Any]:
    return {
        "channel": str(instance.channel),
        "post": str(instance.post),
        "content": instance.content,
    }
