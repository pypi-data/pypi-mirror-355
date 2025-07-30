# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "HASH_SIZE",
    "HASH_LENGTH",
    "Hash",
)

import typing

import attrs
from attrs.validators import min_len, max_len
from blake3 import blake3

from pletyvo.internal.base64 import b64decodenopad, b64encodenopad


HASH_SIZE: typing.Final[int] = 32
HASH_LENGTH: typing.Final[int] = 43


def _len_eq(n: int):
    return min_len(n), max_len(n)


@attrs.define(hash=True)
class Hash:
    data: bytes = attrs.field(validator=_len_eq(HASH_SIZE))

    def __str__(self) -> str:
        return b64encodenopad(bytes(self))

    def __len__(self) -> int:
        return len(str(self))

    def __bytes__(self) -> bytes:
        return self.data

    @classmethod
    def from_str(cls, s: str) -> Hash:
        if len(s) != HASH_LENGTH:
            error_message = f"Hash must have {HASH_LENGTH} characters, not {len(s)}"
            raise ValueError(error_message)
        return cls(b64decodenopad(s))

    @classmethod
    def gen(cls, sch: int, data: bytes) -> Hash:
        data = bytes((sch,)) + data
        data = blake3(data).digest(length=32)
        return cls(data)
