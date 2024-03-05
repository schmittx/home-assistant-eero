"""Eero API"""
from __future__ import annotations

from .resource import EeroResource
from .util import generate_qr_code


class EeroBackupNetwork(EeroResource):

    @property
    def auto_join_enabled(self) -> bool | None:
        return self.data.get("enabled")

    @auto_join_enabled.setter
    def auto_join_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=self.url,
            json={
                "enabled": value,
                "ssid": self.ssid,
                "password": self.password,
            },
        )

    @property
    def backup_access_point_id(self) -> str | None:
        return self.data.get("connectivity", {}).get("backup_access_point_id")

    @property
    def checked(self) -> str | None:
        return self.data.get("connectivity", {}).get("checked")

    @property
    def created(self) -> str | None:
        return self.data.get("created")

    @property
    def failure_reason(self) -> str | None:
        return self.data.get("connectivity", {}).get("failure_reason")

    @property
    def id(self) -> str | None:
        return self.uuid

    @property
    def last_updated_at(self) -> str | None:
        return self.data.get("last_updated_at")

    @property
    def name(self) -> str | None:
        return self.ssid

    @property
    def password(self) -> str | None:
        return self.data.get("password")

    @property
    def qr_code(self) -> bytes | None:
        if all(
            [
                not self.auto_join_enabled,
                self.api.default_qr_code,
            ]
        ):
            return self.api.default_qr_code
        return generate_qr_code(
            ssid=self.ssid,
            password=self.password,
        )

    @property
    def ssid(self) -> str | None:
        return self.data.get("ssid")

    @property
    def status(self) -> str | None:
        return self.data.get("connectivity", {}).get("status")

    @property
    def uuid(self) -> str | None:
        return self.data.get("uuid")
