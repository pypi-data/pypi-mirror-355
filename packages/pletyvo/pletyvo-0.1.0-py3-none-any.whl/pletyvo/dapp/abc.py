# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: t.Sequence[str] = (
    "Signer",
    "HashService",
    "EventService",
)

import typing as t

if t.TYPE_CHECKING:
    from .hash import Hash
    from .event import (
        Event,
        AuthHeader,
        EventInput,
        EventResponse,
    )
    from pletyvo.types import (
        UUIDLike,
        QueryOption,
    )


class Signer(t.Protocol):
    @property
    def sch(cls) -> int:
        raise NotImplementedError

    def sign(self, msg: bytes) -> bytes:
        raise NotImplementedError

    @property
    def pub(self) -> bytes:
        raise NotImplementedError

    @property
    def hash(self) -> Hash:
        raise NotImplementedError

    def auth(self, msg: bytes) -> AuthHeader:
        raise NotImplementedError


class HashService(t.Protocol):
    async def get_by_id(self, id: Hash) -> EventResponse:
        raise NotImplementedError


class EventService(t.Protocol):
    async def get(self, option: t.Optional[QueryOption] = None) -> list[Event]:
        raise NotImplementedError

    async def get_by_id(self, id: UUIDLike) -> t.Optional[Event]:
        raise NotImplementedError

    async def create(self, input: EventInput) -> EventResponse:
        raise NotImplementedError
