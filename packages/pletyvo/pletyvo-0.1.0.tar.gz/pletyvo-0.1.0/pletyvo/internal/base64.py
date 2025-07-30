# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "b64encodenopad",
    "b64decodenopad",
)

import typing
from base64 import urlsafe_b64encode, urlsafe_b64decode


def b64encodenopad(data: bytes) -> str:
    return urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64decodenopad(data: str) -> bytes:
    return urlsafe_b64decode(data + "===")
