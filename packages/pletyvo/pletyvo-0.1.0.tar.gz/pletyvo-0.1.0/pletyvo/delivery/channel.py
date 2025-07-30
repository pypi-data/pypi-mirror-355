# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Channel",
    "ChannelCreateInput",
    "ChannelUpdateInput",
)

import typing

import attrs

from pletyvo import dapp
from pletyvo.internal.validators import channel_name_validator
from pletyvo.internal.sanitizer import dapp_hash_converter


@attrs.define
class Channel(dapp.EventHeader):
    name: str = attrs.field(validator=channel_name_validator())

    author: dapp.Hash = attrs.field(converter=dapp_hash_converter)

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> Channel:
        return cls(
            id=d["id"],
            hash=d["hash"],
            author=d["author"],
            name=d["name"],
        )


@attrs.define
class ChannelCreateInput:
    name: str = attrs.field(validator=channel_name_validator())

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> ChannelCreateInput:
        return cls(
            name=d["name"],
        )


@attrs.define
class ChannelUpdateInput:
    name: str = attrs.field(validator=channel_name_validator())

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> ChannelUpdateInput:
        return cls(
            name=d["name"],
        )
