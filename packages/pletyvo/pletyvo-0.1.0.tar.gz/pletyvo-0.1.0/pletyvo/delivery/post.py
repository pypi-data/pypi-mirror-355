# Copyright (c) 2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Post",
    "PostCreateInput",
    "PostUpdateInput",
)

import typing
from uuid import UUID

import attrs

from pletyvo import dapp
from pletyvo.internal.validators import post_content_validator
from pletyvo.internal.sanitizer import (
    uuid_converter,
    dapp_hash_converter,
)


@attrs.define
class Post:
    id: UUID = attrs.field(converter=uuid_converter)

    hash: dapp.Hash = attrs.field(converter=dapp_hash_converter)

    author: dapp.Hash = attrs.field(converter=dapp_hash_converter)

    channel: UUID = attrs.field(converter=uuid_converter)

    content: str = attrs.field(validator=post_content_validator())

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> Post:
        return cls(
            id=d["id"],
            hash=d["hash"],
            author=d["author"],
            channel=d["channel"],
            content=d["content"],
        )


@attrs.define
class PostCreateInput:
    channel: UUID = attrs.field(converter=uuid_converter)

    content: str = attrs.field(validator=post_content_validator())


@attrs.define
class PostUpdateInput:
    channel: UUID = attrs.field(converter=uuid_converter)

    post: dapp.Hash = attrs.field(converter=dapp_hash_converter)

    content: str = attrs.field(validator=post_content_validator())
