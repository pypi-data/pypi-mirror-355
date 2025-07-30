# Copyright (c) 2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "post_content_validator",
    "channel_name_validator",
    "message_content_validator",
    "event_type_octet_validator",
)

import typing

from attrs.validators import min_len, max_len, in_


def len_eq(length: int):
    return min_len(length), max_len(length)


def post_content_validator():
    return min_len(1), max_len(2048)


def channel_name_validator():
    return min_len(1), max_len(40)


def message_content_validator():
    return min_len(1), max_len(2048)


def event_type_octet_validator():
    return in_(range(0, 256))
