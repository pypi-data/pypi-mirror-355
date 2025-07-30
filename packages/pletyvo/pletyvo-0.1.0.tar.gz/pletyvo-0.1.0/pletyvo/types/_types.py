# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "JSONType",
    "UUIDLike",
)

import typing
from uuid import UUID


JSONType = typing.Any

UUIDLike = UUID | str
