"""Eero API."""

from __future__ import annotations

import io

import pyqrcode

from .const import STATE_ACTIVE, STATE_TRIALING


def generate_qr_code(ssid: str, password: str | None) -> bytes | None:
    """Generate QR code."""
    if ssid is None:
        return None
    if password:
        wifi_code = "WIFI:S:{ssid};H:{hidden};T:{auth_type};P:{password};;".format(
            ssid=ssid,
            hidden="false",
            auth_type="WPA/WPA2",
            password=password,
        )
    else:
        wifi_code = "WIFI:S:{ssid};H:{hidden};T:{auth_type};;".format(
            ssid=ssid,
            hidden="false",
            auth_type="nopass",
        )
    qr_stream = io.BytesIO()
    qr_code = pyqrcode.create(wifi_code)
    qr_code.png(qr_stream, scale=5, module_color="#000", background="#FFF")
    return qr_stream.getvalue()


def backup_access_point_ok(capable: bool | None, requirements: dict | None) -> bool:
    """Backup access point OK."""
    return capable and all(bool(value) for value in requirements.values())


def premium_ok(capable: bool | None, status: str | None) -> bool:
    """Premium OK."""
    return all(
        [
            capable,
            status in [STATE_ACTIVE, STATE_TRIALING],
        ]
    )
