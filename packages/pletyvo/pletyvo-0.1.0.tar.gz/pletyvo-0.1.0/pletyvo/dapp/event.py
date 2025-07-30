# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "EventBodyDataType",
    "EventBodyType",
    "EventHeader",
    "EventType",
    "EventBody",
    "AuthHeader",
    "EventInput",
    "Event",
    "EventResponse",
)

import typing
import base64
import json
from uuid import UUID
from enum import IntEnum

import attrs

from .hash import Hash
from pletyvo.internal.base64 import b64decodenopad, b64encodenopad
from pletyvo.internal.validators import (
    event_type_octet_validator,
)
from pletyvo.internal.sanitizer import (
    uuid_converter,
    dapp_hash_converter,
    dapp_event_body_converter,
    dapp_auth_header_converter,
)

if typing.TYPE_CHECKING:
    from . import abc


class EventBodyDataType(IntEnum):
    JSON = 1


class EventBodyType(IntEnum):
    BASIC = 1
    LINKED = 2
    MAX = 3

    @staticmethod
    def get_event_body_size(version: int) -> int:
        return {
            EventBodyType.BASIC: 4,
            EventBodyType.LINKED: 36,
        }[EventBodyType(version)]


@attrs.define
class EventHeader:
    id: UUID = attrs.field(converter=uuid_converter)

    hash: Hash = attrs.field(converter=dapp_hash_converter)

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> EventHeader:
        return cls(
            id=d["id"],
            hash=d["hash"],
        )


@attrs.define
class EventType:
    major: int = attrs.field(validator=event_type_octet_validator())

    minor: int = attrs.field(validator=event_type_octet_validator())

    def __bytes__(self) -> bytes:
        return bytes(tuple(self))

    def __iter__(self) -> typing.Generator[int, typing.Any, None]:
        yield self.major
        yield self.minor

    @classmethod
    def from_uint16(cls, et: int) -> EventType:
        if not (0 <= et <= 0xFFFF):
            error_message = "Event type must be a 16-bit unsigned integer"
            raise ValueError(error_message)
        return cls(et >> 8, et & 0xFF)

    def as_uint16(self) -> int:
        return (self.major << 8) | self.minor

    @classmethod
    def from_bytes(cls, value: bytes) -> EventType:
        if len(value) != 2:
            error_message = "Event type must be a 16-bit unsigned integer"
            raise ValueError(error_message)
        return cls(value[0], value[1])


@attrs.define
class EventBody:
    # TODO: Implement `.from_json(...)` function, consider
    #       `obj.version() >= EventBodyType.MAX` when is time
    #       to do validation.
    # TODO: Since in client-side there is no need to use `.from_json(...)`,
    #       do not implement it for now. Keep it simple, stupid.

    payload: bytearray = attrs.field(validator=attrs.validators.instance_of(bytearray))

    @classmethod
    def create(
        cls,
        version: EventBodyType,
        data_type: EventBodyDataType,
        event_type: EventType,
        value: typing.Any,
    ) -> EventBody:
        if isinstance(data_type, EventBodyDataType) is False:
            error_message = f"Unsupported data type: {data_type}"
            raise ValueError(error_message)

        data = json.dumps(
            obj=value,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        meta_size = EventBodyType.get_event_body_size(version)
        event_body = cls(bytearray(4 + len(data) + meta_size))

        event_body.version = version
        event_body.data_type = data_type
        event_body.event_type = event_type
        event_body.data = data

        return event_body

    @classmethod
    def from_bytearray(cls, value: bytearray) -> EventBody:
        if len(value) < 4:
            error_message = "EventBody must be at least 4 bytes long"
            raise ValueError(error_message)
        obj = cls.__new__(cls)
        obj.payload = value
        return obj

    @classmethod
    def from_bytes(cls, value: bytes) -> EventBody:
        return cls.from_bytearray(bytearray(value))

    @classmethod
    def from_str(cls, s: str) -> EventBody:
        return cls.from_bytes(b64decodenopad(s))

    def __str__(self) -> str:
        return b64encodenopad(bytes(self))

    def __bytes__(self) -> bytes:
        return bytes(self.payload)

    def __hash__(self) -> int:
        return hash(bytes(self))

    @property
    def version(self) -> int:
        return self.payload[0]

    @version.setter
    def version(self, version: int) -> None:
        self.payload[0] = version

    @property
    def data_type(self) -> EventBodyDataType:
        return EventBodyDataType(self.payload[1])

    @data_type.setter
    def data_type(self, data_type: EventBodyDataType) -> None:
        self.payload[1] = data_type

    @property
    def event_type(self) -> EventType:
        # NOTE: Since every call of `.event_type` will return a new `EventType`
        #       object, it will be impact on performance.
        # TODO: In near future, we probably should consider use `.payload[2:4]`
        #       instead of `EventType.from_bytes(self.payload[2:4])` or use
        #       a caching mechanism like @functools.property_cache
        return EventType.from_bytes(self.payload[2:4])

    @event_type.setter
    def event_type(self, event_type: EventType) -> None:
        self.payload[2], self.payload[3] = event_type

    @property
    def data(self) -> bytes:
        return bytes(self)[4:]

    @data.setter
    def data(self, data: bytes) -> None:
        self.payload[4:] = data

    @property
    def parent(self) -> Hash:
        if self.version != EventBodyType.LINKED:
            error_message = "'.parent' is only available for linked EventBody"
            raise ValueError(error_message)
        return Hash(self.payload[4:36])

    @parent.setter
    def parent(self, hash: Hash) -> None:
        if self.version != EventBodyType.LINKED:
            error_message = "'.parent' is only available for linked EventBody"
            raise ValueError(error_message)
        self.payload[4:36] = bytes(hash)


@attrs.define(hash=True)
class AuthHeader:
    sch: int = attrs.field()

    pub: bytes = attrs.field()

    sig: bytes = attrs.field()

    @property
    def author(self) -> Hash:
        return Hash.gen(self.sch, self.pub)

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> AuthHeader:
        return cls(
            sch=d["sch"],
            pub=base64.b64decode(d["pub"]),
            sig=base64.b64decode(d["sig"]),
        )


@attrs.define()
class EventInput:
    body: EventBody = attrs.field(converter=dapp_event_body_converter)

    auth: AuthHeader = attrs.field(converter=dapp_auth_header_converter)

    @classmethod
    def signed(cls, signer: abc.Signer, body: EventBody) -> EventInput:
        return cls(
            body=body,
            auth=signer.auth(bytes(body)),
        )


@attrs.define
class Event:
    id: UUID = attrs.field(converter=uuid_converter)

    body: EventBody = attrs.field(converter=dapp_event_body_converter)

    auth: AuthHeader = attrs.field(converter=dapp_auth_header_converter)

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> Event:
        return cls(
            id=d["id"],
            body=d["body"],
            auth=d["auth"],
        )


@attrs.define
class EventResponse:
    id: UUID = attrs.field(converter=uuid_converter)

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> EventResponse:
        return cls(id=d["id"])
