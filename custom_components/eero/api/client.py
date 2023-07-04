"""Eero API"""
from __future__ import annotations

import logging

from .const import DEVICE_CATEGORY_TYPE_MAP
from .resource import EeroResource

_LOGGER = logging.getLogger(__name__)


class EeroClient(EeroResource):

    @property
    def adblock_day(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_month(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_week(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_day(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_month(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_week(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_day(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_month(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_week(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_day(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_month(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_week(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def connected(self) -> bool | None:
        return self.data.get("connected")

    @property
    def connection_type(self) -> str | None:
        return self.data.get("connection_type")

    @property
    def data_usage_day(self) -> tuple[int | None, int | None]:
        for device in self.network.data.get("activity", {}).get("devices", {}).get("data_usage_day", []):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def data_usage_month(self) -> tuple[int | None, int | None]:
        for device in self.network.data.get("activity", {}).get("devices", {}).get("data_usage_month", []):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def data_usage_week(self) -> tuple[int | None, int | None]:
        for device in self.network.data.get("activity", {}).get("devices", {}).get("data_usage_week", []):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def device_category(self) -> str | None:
        return DEVICE_CATEGORY_TYPE_MAP.get(self.device_type)

    @property
    def device_type(self) -> str | None:
        return self.data.get("device_type")

    @property
    def hostname(self) -> str | None:
        return self.data.get("hostname")

    @property
    def inspected_day(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("devices", {}).get("inspected_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def inspected_month(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("devices", {}).get("inspected_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def inspected_week(self) -> int | None:
        for device in self.network.data.get("activity", {}).get("devices", {}).get("inspected_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def ip(self) -> str | None:
        return self.data.get("ip")

    @property
    def is_guest(self) -> bool | None:
        return self.data.get("is_guest")

    @property
    def is_private(self) -> bool | None:
        return self.data.get("is_private")

    @property
    def last_active(self) -> str | None:
        return self.data.get("last_active")

    @property
    def mac(self) -> str | None:
        return self.data.get("mac")

    @property
    def manufacturer(self) -> str | None:
        return self.data.get("manufacturer")

    @property
    def name(self) -> str | None:
        if self.nickname:
            return self.nickname
        elif self.hostname:
            return self.hostname
        return self.mac

    @property
    def name_connection_type(self) -> str | None:
        if self.connection_type:
            return f"{self.name} ({self.connection_type.title()})"
        return f"{self.name} (Unknown)"

    @property
    def name_mac(self) -> str | None:
        return f"{self.name} ({self.mac})"

    @property
    def nickname(self) -> str | None:
        return self.data.get("nickname")

    @property
    def paused(self) -> bool | None:
        return self.data.get("paused")

    @paused.setter
    def paused(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=f"/2.3/networks/{self.network.id}/devices/{self.mac}",
            json=dict(paused=value),
        )

    @property
    def secondary_wan_deny_access(self) -> bool | None:
        return not self.data.get("secondary_wan_deny_access")

    @secondary_wan_deny_access.setter
    def secondary_wan_deny_access(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=f"/2.3/networks/{self.network.id}/devices/{self.mac}",
            json=dict(secondary_wan_deny_access=bool(not value)),
        )

    @property
    def signal(self) -> int | None:
        if signal := self.data.get("connectivity", {}).get("signal"):
            return int(signal.replace(" dBm", ""))
        return signal

    @property
    def source_location(self) -> str | None:
        return self.data.get("source", {}).get("location")

    @property
    def url_insights(self) -> str | None:
        return f"{self.network.url_insights}/devices/{self.id}"

    @property
    def usage_down(self) -> float:
        if usage := self.data.get("usage"):
            return usage.get("down_mbps", 0)
        return 0

    @property
    def usage_up(self) -> float:
        if usage := self.data.get("usage"):
            return usage.get("up_mbps", 0)
        return 0

    @property
    def wireless(self) -> bool | None:
        return self.data.get("wireless")
