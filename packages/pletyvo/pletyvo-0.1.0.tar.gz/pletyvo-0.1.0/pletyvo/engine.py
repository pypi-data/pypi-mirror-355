# Copyright (c) 2024-2025 Osyah
# SPDX-License-Identifier: MIT

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Config",
    "DefaultEngine",
)

import typing
from functools import cached_property

from aiohttp import ClientSession
import attrs

from . import abc

if typing.TYPE_CHECKING:
    from pletyvo.types import JSONType


_CONTENT_TYPE_KEY: typing.Final[str] = "Content-Type"
_CONTENT_TYPE_JSON: typing.Final[str] = "application/json"

_NETWORK_IDENTIFY_KEY: typing.Final[str] = "Network"


@attrs.define
class Config:
    url: str = attrs.field()

    network: typing.Optional[str] = attrs.field(default=None)


class DefaultEngine(abc.Engine):
    def __init__(self, config: Config):
        self._config = config

    @cached_property
    def session(self) -> ClientSession:
        session = ClientSession(
            base_url=self._config.url,
            raise_for_status=True,
        )

        if network := self._config.network:
            session.headers[_NETWORK_IDENTIFY_KEY] = network

        return session

    async def get(self, endpoint: str) -> JSONType:
        async with self.session.get(endpoint) as response:
            return await response.json()

    async def post(self, endpoint: str, body: JSONType) -> JSONType:
        headers = {_CONTENT_TYPE_KEY: _CONTENT_TYPE_JSON}
        async with self.session.post(endpoint, json=body, headers=headers) as response:
            return await response.json()
