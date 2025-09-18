"""Eero API."""

from __future__ import annotations

from datetime import datetime
import logging

from .const import DEVICE_CATEGORY_TYPE_MAP, METHOD_PUT
from .resource import EeroResource

_LOGGER = logging.getLogger(__name__)


class EeroClient(EeroResource):
    """EeroClient."""

    @property
    def adblock_day(self) -> int | None:
        """Adblock day."""
        for device in (
            self.network.data.get("activity", {})
            .get("network", {})
            .get("adblock_day", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_month(self) -> int | None:
        """Adblock month."""
        for device in (
            self.network.data.get("activity", {})
            .get("network", {})
            .get("adblock_month", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_week(self) -> int | None:
        """Adblock week."""
        for device in (
            self.network.data.get("activity", {})
            .get("network", {})
            .get("adblock_week", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_day(self) -> int | None:
        """Blocked day."""
        for device in (
            self.network.data.get("activity", {})
            .get("network", {})
            .get("blocked_day", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_month(self) -> int | None:
        """Blocked month."""
        for device in (
            self.network.data.get("activity", {})
            .get("network", {})
            .get("blocked_month", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_week(self) -> int | None:
        """Blocked week."""
        for device in (
            self.network.data.get("activity", {})
            .get("network", {})
            .get("blocked_week", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def channel(self) -> int | None:
        """Channel."""
        return self.data.get("channel")

    @property
    def channel_width_rx(self) -> str | None:
        """Channel width RX."""
        return (
            self.data.get("connectivity", {})
            .get("rx_rate_info", {})
            .get("channel_width")
        )

    @property
    def channel_width_tx(self) -> str | None:
        """Channel width TX."""
        return (
            self.data.get("connectivity", {})
            .get("tx_rate_info", {})
            .get("channel_width")
        )

    @property
    def connected(self) -> bool | None:
        """Connected."""
        return self.data.get("connected")

    @property
    def connection_type(self) -> str | None:
        """Connection type."""
        return self.data.get("connection_type")

    @property
    def data_usage_day(self) -> tuple[int | None, int | None]:
        """Data usage day."""
        for device in (
            self.network.data.get("activity", {})
            .get("devices", {})
            .get("data_usage_day", [])
        ):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def data_usage_month(self) -> tuple[int | None, int | None]:
        """Data usage month."""
        for device in (
            self.network.data.get("activity", {})
            .get("devices", {})
            .get("data_usage_month", [])
        ):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def data_usage_week(self) -> tuple[int | None, int | None]:
        """Data usage week."""
        for device in (
            self.network.data.get("activity", {})
            .get("devices", {})
            .get("data_usage_week", [])
        ):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def device_category(self) -> str | None:
        """Device category."""
        return DEVICE_CATEGORY_TYPE_MAP.get(self.device_type)

    @property
    def device_type(self) -> str | None:
        """Device type."""
        return self.data.get("device_type")

    @property
    def hostname(self) -> str | None:
        """Hostname."""
        return self.data.get("hostname")

    @property
    def inspected_day(self) -> int | None:
        """Inspected day."""
        for device in (
            self.network.data.get("activity", {})
            .get("devices", {})
            .get("inspected_day", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def inspected_month(self) -> int | None:
        """Inspected month."""
        for device in (
            self.network.data.get("activity", {})
            .get("devices", {})
            .get("inspected_month", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def inspected_week(self) -> int | None:
        """Inspected week."""
        for device in (
            self.network.data.get("activity", {})
            .get("devices", {})
            .get("inspected_week", [])
        ):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def interface_frequency(self) -> tuple[str | None, str | None]:
        """Interface frequency."""
        return (
            self.data.get("interface", {}).get("frequency"),
            self.data.get("interface", {}).get("frequency_unit"),
        )

    @property
    def ip(self) -> str | None:
        """IP."""
        return self.data.get("ip")

    @property
    def is_guest(self) -> bool | None:
        """Is guest."""
        return self.data.get("is_guest")

    @property
    def is_private(self) -> bool | None:
        """Is private."""
        return self.data.get("is_private")

    @property
    def last_active(self) -> datetime | None:
        """Last active."""
        if last_active := self.data.get("last_active"):
            return datetime.fromisoformat(last_active)
        return None

    @property
    def mac(self) -> str | None:
        """MAC."""
        return self.data.get("mac")

    @property
    def manufacturer(self) -> str | None:
        """Manufacturer."""
        return self.data.get("manufacturer")

    @property
    def name(self) -> str | None:
        """Name."""
        if self.nickname:
            return self.nickname
        if self.hostname:
            return self.hostname
        return self.mac

    @property
    def name_connection_type(self) -> str | None:
        """Name connection type."""
        if self.connection_type:
            return f"{self.name} ({self.connection_type.title()})"
        return f"{self.name} (Unknown)"

    @property
    def name_mac(self) -> str | None:
        """Name MAC."""
        return f"{self.name} ({self.mac})"

    @property
    def nickname(self) -> str | None:
        """Nickname."""
        return self.data.get("nickname")

    @property
    def paused(self) -> bool | None:
        """Paused."""
        return self.data.get("paused")

    @paused.setter
    def paused(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=f"/2.3/networks/{self.network.id}/devices/{self.mac}",
            json={"paused": value},
        )

    @property
    def secondary_wan_deny_access(self) -> bool | None:
        """Secondary WAN deny access."""
        return not self.data.get("secondary_wan_deny_access")

    @secondary_wan_deny_access.setter
    def secondary_wan_deny_access(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=f"/2.3/networks/{self.network.id}/devices/{self.mac}",
            json={"secondary_wan_deny_access": bool(not value)},
        )

    @property
    def signal(self) -> tuple[int | None, str | None]:
        """Signal."""
        if signal := self.data.get("connectivity", {}).get("signal"):
            return (
                int(signal.split()[0]),
                signal.split()[1],
            )
        return (None, None)

    @property
    def source_location(self) -> str | None:
        """Source location."""
        return self.data.get("source", {}).get("location")

    @property
    def url_insights(self) -> str | None:
        """URL insights."""
        return f"{self.network.url_insights}/devices/{self.id}"

    @property
    def usage_down(self) -> float:
        """Usage down."""
        if usage := self.data.get("usage"):
            return usage.get("down_mbps", 0)
        return 0

    @property
    def usage_up(self) -> float:
        """Usage up."""
        if usage := self.data.get("usage"):
            return usage.get("up_mbps", 0)
        return 0

    @property
    def wireless(self) -> bool | None:
        """Wireless."""
        return self.data.get("wireless")
