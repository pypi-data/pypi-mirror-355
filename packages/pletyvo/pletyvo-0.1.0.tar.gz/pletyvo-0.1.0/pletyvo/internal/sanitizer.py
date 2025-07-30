# Copyright (c) 2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "dapp_hash_converter",
    "dapp_auth_header_converter",
    "dapp_event_body_converter",
    "uuid_converter",
)

import typing
import datetime as dt
from uuid import UUID

from .uuid import uuid7

if typing.TYPE_CHECKING:
    from pletyvo.dapp.event import Hash, AuthHeader, EventBody

    from pletyvo.types import UUIDLike


def dapp_hash_converter(h: Hash | str) -> Hash:
    from pletyvo.dapp.event import Hash

    if isinstance(h, str):
        return Hash.from_str(h)
    return h


def dapp_auth_header_converter(
    d: AuthHeader | dict[str, typing.Any],
) -> AuthHeader:
    from pletyvo.dapp.event import AuthHeader

    if isinstance(d, dict):
        return AuthHeader.from_dict(d)
    return d


def dapp_event_body_converter(
    b: EventBody | str | bytes | bytearray,
) -> EventBody:
    from pletyvo.dapp.event import EventBody

    if isinstance(b, str):
        return EventBody.from_str(b)
    elif isinstance(b, bytes):
        return EventBody.from_bytes(b)
    elif isinstance(b, bytearray):
        return EventBody.from_bytearray(b)
    elif isinstance(b, memoryview):
        return dapp_event_body_converter(b.tobytes())
    return b


def uuid_converter(u: UUIDLike | dt.datetime) -> UUID:
    if isinstance(u, UUID):
        return u
    elif isinstance(u, str):
        return UUID(u)
    elif isinstance(u, dt.datetime):
        return uuid7(timestamp=u.timestamp())
    return u
