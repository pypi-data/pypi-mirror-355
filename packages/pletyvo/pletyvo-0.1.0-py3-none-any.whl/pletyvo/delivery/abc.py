# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: t.Sequence[str] = (
    "ChannelService",
    "MessageService",
    "PostService",
)

import typing as t

if t.TYPE_CHECKING:
    from pletyvo.types import (
        QueryOption,
        UUIDLike,
    )
    from pletyvo import dapp
    from .channel import (
        Channel,
        ChannelCreateInput,
        ChannelUpdateInput,
    )
    from .post import (
        Post,
        PostCreateInput,
        PostUpdateInput,
    )
    from .message import (
        Message,
    )


class ChannelService(t.Protocol):
    async def get_by_id(self, id: UUIDLike) -> Channel:
        raise NotImplementedError

    async def create(self, input: ChannelCreateInput) -> dapp.EventResponse:
        raise NotImplementedError

    async def update(self, input: ChannelUpdateInput) -> dapp.EventResponse:
        raise NotImplementedError


class MessageService(t.Protocol):
    async def get(
        self, channel: UUIDLike, option: t.Optional[QueryOption] = None
    ) -> list[Message]:
        raise NotImplementedError

    async def get_by_id(self, channel: UUIDLike, id: UUIDLike) -> t.Optional[Message]:
        raise NotImplementedError

    async def send(self, message: dapp.EventInput) -> None:
        raise NotImplementedError


class PostService(t.Protocol):
    async def get(
        self, channel: UUIDLike, option: t.Optional[QueryOption] = None
    ) -> list[Post]:
        raise NotImplementedError

    async def get_by_id(self, channel: UUIDLike, id: UUIDLike) -> Post:
        raise NotImplementedError

    async def create(self, input: PostCreateInput) -> dapp.EventResponse:
        raise NotImplementedError

    async def update(self, input: PostUpdateInput) -> dapp.EventResponse:
        raise NotImplementedError
