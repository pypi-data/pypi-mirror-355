# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "CHANNEL_CREATE_EVENT_TYPE",
    "CHANNEL_UPDATE_EVENT_TYPE",
    "POST_CREATE_EVENT_TYPE",
    "POST_UPDATE_EVENT_TYPE",
    "MESSAGE_CREATE_EVENT_TYPE",
)

import typing

from pletyvo.dapp import EventType


CHANNEL_CREATE_EVENT_TYPE = EventType.from_uint16(3)
CHANNEL_UPDATE_EVENT_TYPE = EventType.from_uint16(4)

POST_CREATE_EVENT_TYPE = EventType.from_uint16(5)
POST_UPDATE_EVENT_TYPE = EventType.from_uint16(6)

MESSAGE_CREATE_EVENT_TYPE = EventType.from_uint16(768)
