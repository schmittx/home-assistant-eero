"""Eero API."""

from __future__ import annotations

from .const import METHOD_PUT
from .resource import EeroResource
from .util import generate_qr_code


class EeroBackupNetwork(EeroResource):
    """EeroBackupNetwork."""

    @property
    def auto_join_enabled(self) -> bool | None:
        """Auto join enabled."""
        return self.data.get("enabled")

    @auto_join_enabled.setter
    def auto_join_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=self.url,
            json={
                "enabled": value,
                "ssid": self.ssid,
                "password": self.password,
            },
        )

    @property
    def backup_access_point_id(self) -> str | None:
        """Backup access point."""
        return self.data.get("connectivity", {}).get("backup_access_point_id")

    @property
    def checked(self) -> str | None:
        """Checked."""
        return self.data.get("connectivity", {}).get("checked")

    @property
    def created(self) -> str | None:
        """Created."""
        return self.data.get("created")

    @property
    def failure_reason(self) -> str | None:
        """Failure reason."""
        return self.data.get("connectivity", {}).get("failure_reason")

    @property
    def id(self) -> str | None:
        """ID."""
        return self.uuid

    @property
    def last_updated_at(self) -> str | None:
        """Last updated at."""
        return self.data.get("last_updated_at")

    @property
    def name(self) -> str | None:
        """Name."""
        return self.ssid

    @property
    def password(self) -> str | None:
        """Password."""
        return self.data.get("password")

    @property
    def qr_code(self) -> bytes | None:
        """QR code."""
        if all(
            [
                not self.auto_join_enabled,
                self.api.show_eero_logo.get(self.network.id),
            ]
        ):
            return self.api.default_qr_code
        return generate_qr_code(
            ssid=self.ssid,
            password=self.password,
        )

    @property
    def ssid(self) -> str | None:
        """SSID."""
        return self.data.get("ssid")

    @property
    def status(self) -> str | None:
        """Status."""
        return self.data.get("connectivity", {}).get("status")

    @property
    def uuid(self) -> str | None:
        """UUID."""
        return self.data.get("uuid")
