# Copyright (c) 2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = ("uuid7",)

import typing
from uuid import UUID
from uuid_utils import uuid7 as uu_uuid7
from uuid_utils.compat import uuid7 as uuc_uuid7


def uuid7(
    timestamp: typing.Optional[float] = None,
) -> UUID:
    if not timestamp:
        return uuc_uuid7()

    ts, ns = _split_timestamp(timestamp)
    return UUID(int=uu_uuid7(ts, ns).int)


def _split_timestamp(timestamp: float) -> tuple[int, int]:
    ts, ns = divmod(timestamp, 1)
    ts, ns = round(ts), round((ns % 1) * 1_000_000_000)
    return ts, ns
