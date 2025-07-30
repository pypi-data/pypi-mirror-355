# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: t.Sequence[str] = ("Engine",)

import typing as t

if t.TYPE_CHECKING:
    from pletyvo.types import JSONType


class Engine(t.Protocol):
    async def get(self, endpoint: str) -> JSONType:
        raise NotImplementedError

    async def post(self, endpoint: str, body: JSONType) -> JSONType:
        raise NotImplementedError
