"""Eero API."""

from __future__ import annotations

from .const import URL_ACCOUNT


class EeroResource:
    """EeroResource."""

    def __init__(self, api, network, data) -> None:
        """Initialize."""
        self.api = api
        self.network = network
        self.data = data

    @property
    def id(self) -> str | None:
        """ID."""
        if self.is_network:
            return self.url.replace("/2.2/networks/", "")
        if self.is_eero:
            return self.url.replace("/2.2/eeros/", "")
        if self.is_profile:
            return self.url.replace(f"{self.network.url}/profiles/", "")
        if self.is_client:
            return self.url.replace(f"{self.network.url}/devices/", "")
        return None

    @property
    def is_account(self) -> bool:
        """Is account."""
        return bool(self.__class__.__name__ == "EeroAccount")

    @property
    def is_backup_network(self) -> bool:
        """Is backup network."""
        return bool(self.__class__.__name__ == "EeroBackupNetwork")

    @property
    def is_client(self) -> bool:
        """Is client."""
        return bool(self.__class__.__name__ == "EeroClient")

    @property
    def is_eero(self) -> bool:
        """Is Eero."""
        return bool(self.__class__.__name__ in ["EeroDevice", "EeroDeviceBeacon"])

    @property
    def is_eero_beacon(self) -> bool:
        """Is Eero beacon."""
        return bool(self.__class__.__name__ == "EeroDeviceBeacon")

    @property
    def is_network(self) -> bool:
        """Is network."""
        return bool(self.__class__.__name__ == "EeroNetwork")

    @property
    def is_profile(self) -> bool:
        """Is profile."""
        return bool(self.__class__.__name__ == "EeroProfile")

    @property
    def url(self) -> str | None:
        """URL."""
        if self.is_account:
            return URL_ACCOUNT
        if self.is_backup_network:
            uuid = self.data.get("uuid")
            return f"{self.network.url}/backup_access_points/{uuid}"
        return self.data.get("url")
