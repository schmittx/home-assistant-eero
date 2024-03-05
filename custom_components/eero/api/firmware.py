"""Eero API"""
from __future__ import annotations


class EeroFirmware(object):

    def __init__(self, data: dict =  {}) -> None:
        self.data = data

    @property
    def features(self) -> list[str | None] | None:
        return self.data.get("features")

    @property
    def os_version(self) -> str | None:
        return self.data.get("os_version")

    @property
    def release_date(self) -> str | None:
        return self.data.get("release_date")

    @property
    def title(self) -> str | None:
        return self.data.get("title")
