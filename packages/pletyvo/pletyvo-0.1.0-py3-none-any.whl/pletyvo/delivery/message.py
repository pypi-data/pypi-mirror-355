# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Message",
    "MessageInput",
)

import typing
from uuid import UUID

import attrs

from pletyvo import dapp
from pletyvo.internal.validators import message_content_validator
from pletyvo.internal.sanitizer import (
    dapp_hash_converter,
    dapp_auth_header_converter,
    dapp_event_body_converter,
    uuid_converter,
)


@attrs.define(hash=True)
class Message:
    body: dapp.EventBody = attrs.field(converter=dapp_event_body_converter)

    auth: dapp.AuthHeader = attrs.field(converter=dapp_auth_header_converter)

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> Message:
        return cls(
            body=d["body"],
            auth=d["auth"],
        )


@attrs.define
class MessageInput:
    id: UUID = attrs.field(converter=uuid_converter)

    channel: dapp.Hash = attrs.field(converter=dapp_hash_converter)

    content: str = attrs.field(validator=message_content_validator())
