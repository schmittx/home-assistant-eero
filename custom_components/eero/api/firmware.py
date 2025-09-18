"""Eero API."""

from __future__ import annotations


class EeroFirmware:
    """EeroFirmware."""

    def __init__(self, data: dict | None = None) -> None:
        """Initialize."""
        self.data = data
        if self.data is None:
            self.data = {}

    @property
    def features(self) -> list[str | None] | None:
        """Features."""
        return self.data.get("features")

    @property
    def os_version(self) -> str | None:
        """OS version."""
        return self.data.get("os_version")

    @property
    def release_date(self) -> str | None:
        """Release date."""
        return self.data.get("release_date")

    @property
    def title(self) -> str | None:
        """Title."""
        return self.data.get("title")
