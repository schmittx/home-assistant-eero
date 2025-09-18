"""Eero API."""

from __future__ import annotations

from datetime import datetime

from .client import EeroClient
from .const import METHOD_POST, METHOD_PUT
from .resource import EeroResource


class EeroProfile(EeroResource):
    """EeroProfile."""

    @property
    def ad_block(self) -> bool:
        """Ad block."""
        return all(
            [
                self.network.ad_block_enabled,
                self.url in self.network.ad_block_profiles,
            ]
        )

    @ad_block.setter
    def ad_block(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        profiles = self.network.ad_block_profiles
        if value:
            profiles.append(self.url)
        else:
            profiles.remove(self.url)
            if profiles:
                value = True
        self.api.call(
            method=METHOD_POST,
            url=f"{self.network.url_dns_policies}/adblock",
            json={
                "enable": value,
                "profiles": profiles,
            },
        )

    @property
    def adblock_day(self) -> int | None:
        """Adblock day."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("adblock_day", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def adblock_month(self) -> int | None:
        """Adblock month."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("adblock_month", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def adblock_week(self) -> int | None:
        """Adblock week."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("adblock_week", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def block_apps_enabled(self) -> bool:
        """Block apps enabled."""
        return bool(self.blocked_applications)

    @property
    def block_gaming_content(self) -> bool | None:
        """Block gaming content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_gaming_content")
        )

    @block_gaming_content.setter
    def block_gaming_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_gaming_content": value,
            },
        )

    @property
    def block_illegal_content(self) -> bool | None:
        """Block illegal content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_illegal_content")
        )

    @block_illegal_content.setter
    def block_illegal_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_illegal_content": value,
            },
        )

    @property
    def block_messaging_content(self) -> bool | None:
        """Block messaging content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_messaging_content")
        )

    @block_messaging_content.setter
    def block_messaging_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_messaging_content": value,
            },
        )

    @property
    def block_pornographic_content(self) -> bool | None:
        """Block pornographic content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_pornographic_content")
        )

    @block_pornographic_content.setter
    def block_pornographic_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_pornographic_content": value,
            },
        )

    @property
    def block_shopping_content(self) -> bool | None:
        """Block shopping content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_shopping_content")
        )

    @block_shopping_content.setter
    def block_shopping_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_shopping_content": value,
            },
        )

    @property
    def block_social_content(self) -> bool | None:
        """Block social content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_social_content")
        )

    @block_social_content.setter
    def block_social_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_social_content": value,
            },
        )

    @property
    def block_streaming_content(self) -> bool | None:
        """Block streaming content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_streaming_content")
        )

    @block_streaming_content.setter
    def block_streaming_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_streaming_content": value,
            },
        )

    @property
    def block_violent_content(self) -> bool | None:
        """Block violent content."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("block_violent_content")
        )

    @block_violent_content.setter
    def block_violent_content(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "block_violent_content": value,
            },
        )

    @property
    def blocked_applications(self) -> list[str]:
        """Blocked applications."""
        return self.data.get("premium_dns", {}).get("blocked_applications", [])

    @property
    def blocked_applications_count(self) -> int:
        """Blocked applications count."""
        return len(self.blocked_applications)

    def set_blocked_applications(self, blocked_applications: list) -> None:
        """Set blocked application."""
        if not isinstance(blocked_applications, list):
            return
        self.api.call(
            method=METHOD_PUT,
            url=f"{self.url_dns_policies}/applications/blocked",
            json={
                "applications": blocked_applications,
            },
        )

    @property
    def blocked_day(self) -> int | None:
        """Blocked day."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("blocked_day", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def blocked_month(self) -> int | None:
        """Blocked month."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("blocked_month", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def blocked_week(self) -> int | None:
        """Blocked week."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("blocked_week", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def connected(self) -> bool:
        """Connected."""
        return bool(self.connected_clients_count != 0)

    @property
    def connected_clients_count(self) -> int:
        """Connected clients count."""
        return len(self.connected_clients_names)

    @property
    def connected_clients_names(self) -> list[str]:
        """Connected clients names."""
        return [client.name for client in self.clients if client.connected]

    @property
    def data_usage_day(self) -> tuple[int | None, int | None]:
        """Data usage day."""
        down, up = None, None
        for series in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("data_usage_day", {})
            .get(self.id, [])
        ):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def data_usage_month(self) -> tuple[int | None, int | None]:
        """Data usage month."""
        down, up = None, None
        for series in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("data_usage_month", {})
            .get(self.id, [])
        ):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def data_usage_week(self) -> tuple[int | None, int | None]:
        """Data usage week."""
        down, up = None, None
        for series in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("data_usage_week", {})
            .get(self.id, [])
        ):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def inspected_day(self) -> int | None:
        """Inspected day."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("inspected_day", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def inspected_month(self) -> int | None:
        """Inspected month."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("inspected_month", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def inspected_week(self) -> int | None:
        """Inspected week."""
        for profile in (
            self.network.data.get("activity", {})
            .get("profiles", {})
            .get("inspected_week", [])
        ):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def last_active(self) -> datetime | None:
        """Last active."""
        if last_active := [
            client.last_active
            for client in self.clients
            if client.last_active is not None
        ]:
            return max(last_active)
        return None

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def name_long(self) -> str:
        """Name long."""
        return f"{self.name} Profile"

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
            url=self.url,
            json={
                "paused": value,
            },
        )

    @property
    def safe_search_enabled(self) -> bool | None:
        """Safe search enabled."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("safe_search_enabled")
        )

    @safe_search_enabled.setter
    def safe_search_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "safe_search_enabled": value,
            },
        )

    @property
    def url_dns_policies(self) -> str | None:
        """URL DNS policies."""
        return f"{self.network.url}/dns_policies/profiles/{self.id}"

    @property
    def url_insights(self) -> str | None:
        """URL insights."""
        return f"{self.network.url_insights}/profiles/{self.id}"

    @property
    def youtube_restricted(self) -> bool | None:
        """YouTube restricted."""
        return (
            self.data.get("unified_content_filters", {})
            .get("dns_policies", {})
            .get("youtube_restricted")
        )

    @youtube_restricted.setter
    def youtube_restricted(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=self.url_dns_policies,
            json={
                "youtube_restricted": value,
            },
        )

    @property
    def clients(self) -> list[EeroClient | None]:
        """Clients."""
        return [
            EeroClient(self.api, self, client)
            for client in self.data.get("devices", [])
        ]
