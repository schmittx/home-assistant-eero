"""Eero API."""

from __future__ import annotations

from .backup_network import EeroBackupNetwork
from .client import EeroClient
from .const import (
    DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_CATEGORY_HOME,
    DEVICE_CATEGORY_OTHER,
    METHOD_DELETE,
    METHOD_POST,
    METHOD_PUT,
    MODEL_BEACON,
    PREFERRED_UPDATE_HOUR_MAP,
    STATE_DISABLED,
    STATE_NETWORK,
    STATE_PROFILE,
)
from .eero import EeroDevice, EeroDeviceBeacon
from .firmware import EeroFirmware
from .profile import EeroProfile
from .resource import EeroResource
from .util import generate_qr_code, premium_ok


class EeroNetwork(EeroResource):
    """EeroNetwork."""

    def __init__(self, api, account, data) -> None:
        """Initialize."""
        super().__init__(api=api, network=None, data=data)
        self.account = account
        if self.data is None:
            self.data = {}

    @property
    def ad_block(self) -> bool:
        """Ad block."""
        return all(
            [
                self.ad_block_enabled,
                not self.ad_block_profiles,
            ]
        )

    @ad_block.setter
    def ad_block(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=f"{self.url_dns_policies}/adblock",
            json={
                "enable": value,
            },
        )

    @property
    def ad_block_enabled(self) -> bool | None:
        """Ad block enabled."""
        return (
            self.data.get("premium_dns", {}).get("ad_block_settings", {}).get("enabled")
        )

    @property
    def ad_block_profiles(self) -> list[str | None] | None:
        """Ad block profiles."""
        return (
            self.data.get("premium_dns", {})
            .get("ad_block_settings", {})
            .get("profiles")
        )

    @property
    def ad_block_status(self) -> str:
        """Ad block status."""
        if self.ad_block:
            return STATE_NETWORK
        if self.ad_block_profiles:
            return STATE_PROFILE
        return STATE_DISABLED

    @property
    def adblock_day(self) -> int | None:
        """Adblock dasy."""
        for series in (
            self.data.get("activity", {}).get("network", {}).get("adblock_day", [])
        ):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def adblock_month(self) -> int | None:
        """Adblock month."""
        for series in (
            self.data.get("activity", {}).get("network", {}).get("adblock_month", [])
        ):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def adblock_week(self) -> int | None:
        """Adblock week."""
        for series in (
            self.data.get("activity", {}).get("network", {}).get("adblock_week", [])
        ):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def backup_internet_enabled(self) -> bool | None:
        """Backup internet enabled."""
        return self.data.get("backup_internet_enabled")

    @backup_internet_enabled.setter
    def backup_internet_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=f"{self.url}/backupinternet",
            json={
                "backup_internet_enabled": value,
            },
        )

    @property
    def band_steering(self) -> bool | None:
        """Band steering."""
        return self.data.get("band_steering")

    @band_steering.setter
    def band_steering(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=self.url_settings,
            json={
                "band_steering": value,
            },
        )

    @property
    def block_malware(self) -> bool | None:
        """Block malware."""
        return (
            self.data.get("premium_dns", {})
            .get("dns_policies", {})
            .get("block_malware")
        )

    @block_malware.setter
    def block_malware(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_POST,
            url=f"{self.url_dns_policies}/network",
            json={
                "block_malware": value,
            },
        )

    @property
    def blocked_day(self) -> dict[str, int | None]:
        """Blocked day."""
        data = {
            "blocked": None,
            "botnet": None,
            "domains": None,
            "malware": None,
            "parked": None,
            "phishing": None,
            "spyware": None,
        }
        for series in (
            self.data.get("activity", {}).get("network", {}).get("blocked_day", [])
        ):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def blocked_month(self) -> dict[str, int | None]:
        """Blocked month."""
        data = {
            "blocked": None,
            "botnet": None,
            "domains": None,
            "malware": None,
            "parked": None,
            "phishing": None,
            "spyware": None,
        }
        for series in (
            self.data.get("activity", {}).get("network", {}).get("blocked_month", [])
        ):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def blocked_week(self) -> dict[str, int | None]:
        """Blocked week."""
        data = {
            "blocked": None,
            "botnet": None,
            "domains": None,
            "malware": None,
            "parked": None,
            "phishing": None,
            "spyware": None,
        }
        for series in (
            self.data.get("activity", {}).get("network", {}).get("blocked_week", [])
        ):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def city(self) -> str | None:
        """City."""
        return self.data.get("geo_ip", {}).get("city")

    @property
    def clients_count(self) -> int | None:
        """Clients count."""
        return self.data.get("clients", {}).get("count")

    @property
    def connected_clients_count(self) -> int:
        """Connected clients count."""
        return len([client for client in self.clients if client.connected])

    @property
    def connected_clients_count_computers_personal(self) -> int:
        """Connected clients count computers personal."""
        return len(
            [
                client
                for client in self.clients
                if client.connected
                and client.device_category == DEVICE_CATEGORY_COMPUTERS_PERSONAL
            ]
        )

    @property
    def connected_clients_count_entertainment(self) -> int:
        """Connected clients count entertainment."""
        return len(
            [
                client
                for client in self.clients
                if client.connected
                and client.device_category == DEVICE_CATEGORY_ENTERTAINMENT
            ]
        )

    @property
    def connected_clients_count_home(self) -> int:
        """Connected clients count home."""
        return len(
            [
                client
                for client in self.clients
                if client.connected and client.device_category == DEVICE_CATEGORY_HOME
            ]
        )

    @property
    def connected_clients_count_other(self) -> int:
        """Connected clients count other."""
        return len(
            [
                client
                for client in self.clients
                if client.connected and client.device_category == DEVICE_CATEGORY_OTHER
            ]
        )

    @property
    def connected_guest_clients_count(self) -> int:
        """Connected guest clients count."""
        return len(
            [client for client in self.clients if client.connected and client.is_guest]
        )

    @property
    def connected_guest_clients_count_computers_personal(self) -> int:
        """Connected guest clients count computers personal."""
        return len(
            [
                client
                for client in self.clients
                if client.connected
                and client.is_guest
                and client.device_category == DEVICE_CATEGORY_COMPUTERS_PERSONAL
            ]
        )

    @property
    def connected_guest_clients_count_entertainment(self) -> int:
        """Connected guest clients count entertainment."""
        return len(
            [
                client
                for client in self.clients
                if client.connected
                and client.is_guest
                and client.device_category == DEVICE_CATEGORY_ENTERTAINMENT
            ]
        )

    @property
    def connected_guest_clients_count_home(self) -> int:
        """Connected guest clients count home."""
        return len(
            [
                client
                for client in self.clients
                if client.connected
                and client.is_guest
                and client.device_category == DEVICE_CATEGORY_HOME
            ]
        )

    @property
    def connected_guest_clients_count_other(self) -> int:
        """Connected guest clients count other."""
        return len(
            [
                client
                for client in self.clients
                if client.connected
                and client.is_guest
                and client.device_category == DEVICE_CATEGORY_OTHER
            ]
        )

    @property
    def country_code(self) -> str | None:
        """Country code."""
        return self.data.get("geo_ip", {}).get("countryCode")

    @property
    def country_name(self) -> str | None:
        """Country name."""
        return self.data.get("geo_ip", {}).get("countryName")

    @property
    def data_usage_day(self) -> tuple[int | None, int | None]:
        """Data usage day."""
        down, up = None, None
        for series in (
            self.data.get("activity", {}).get("network", {}).get("data_usage_day", [])
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
            self.data.get("activity", {}).get("network", {}).get("data_usage_month", [])
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
            self.data.get("activity", {}).get("network", {}).get("data_usage_week", [])
        ):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def ddns_enabled(self) -> bool | None:
        """DDNS enabled."""
        return self.data.get("ddns", {}).get("enabled")

    @ddns_enabled.setter
    def ddns_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        target = "enable" if value else "disable"
        self.api.call(
            method=METHOD_PUT,
            url=f"/2.2/networks/{self.id}/ddns/{target}",
        )

    @property
    def ddns_subdomain(self) -> str | None:
        """DDNS subdomain."""
        return self.data.get("ddns", {}).get("subdomain")

    @property
    def dns_caching(self) -> bool | None:
        """DNS caching."""
        return self.data.get("dns", {}).get("caching")

    @dns_caching.setter
    def dns_caching(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=f"/2.2/networks/{self.id}/dns",
            json={
                "caching": value,
            },
        )

    @property
    def firmware_history(self) -> list[EeroFirmware | None]:
        """Firmware history."""
        return [
            EeroFirmware(firmware)
            for firmware in self.data.get("updates", {})
            .get("release_notes", {})
            .get("history", [])
        ]

    @property
    def gateway_ip(self) -> str | None:
        """Gateway IP."""
        return self.data.get("gateway_ip")

    @property
    def gateway_mac_address(self) -> str | None:
        """Gateway MAC address."""
        for eero in self.eeros:
            if eero.is_gateway:
                return eero.mac_address
        return None

    @property
    def gateway_name(self) -> str | None:
        """Gateway name."""
        for eero in self.eeros:
            if eero.is_gateway:
                return eero.name
        return None

    @property
    def guest_network_enabled(self) -> bool | None:
        """Guest network enabled."""
        return self.data.get("guest_network", {}).get("enabled")

    @guest_network_enabled.setter
    def guest_network_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=f"/2.2/networks/{self.id}/guestnetwork",
            json={
                "enabled": value,
            },
        )

    @property
    def guest_network_name(self) -> str | None:
        """Guest network name."""
        return self.data.get("guest_network", {}).get("name")

    @property
    def guest_network_password(self) -> str | None:
        """Guest network password."""
        return self.data.get("guest_network", {}).get("password")

    @property
    def guest_network_qr_code(self) -> bytes | None:
        """Guest network QR code."""
        if all(
            [
                not self.guest_network_enabled,
                self.api.show_eero_logo.get(self.id),
            ]
        ):
            return self.api.default_qr_code
        return generate_qr_code(
            ssid=self.guest_network_name,
            password=self.guest_network_password,
        )

    @property
    def health_eero_network_status(self) -> str | None:
        """Health Eero network status."""
        return self.data.get("health", {}).get("eero_network", {}).get("status")

    @property
    def health_internet_isp_up(self) -> bool | None:
        """Health internet ISP up."""
        return self.data.get("health", {}).get("internet", {}).get("isp_up")

    @property
    def health_internet_status(self) -> str | None:
        """Health internet status."""
        return self.data.get("health", {}).get("internet", {}).get("status")

    @property
    def inspected_day(self) -> int | None:
        """Inspected day."""
        for series in (
            self.data.get("activity", {}).get("network", {}).get("inspected_day", [])
        ):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def inspected_month(self) -> int | None:
        """Inspected month."""
        for series in (
            self.data.get("activity", {}).get("network", {}).get("inspected_month", [])
        ):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def inspected_week(self) -> int | None:
        """Inspected week."""
        for series in (
            self.data.get("activity", {}).get("network", {}).get("inspected_week", [])
        ):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def ipv6_upstream(self) -> bool | None:
        """IPV6 upstream."""
        return self.data.get("ipv6_upstream")

    @ipv6_upstream.setter
    def ipv6_upstream(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=self.url_settings,
            json={
                "ipv6_upstream": value,
            },
        )

    @property
    def isp(self) -> str | None:
        """ISP."""
        return self.data.get("geo_ip", {}).get("isp")

    @property
    def manifest_resource(self) -> str | None:
        """Manifest resource."""
        return self.data.get("updates", {}).get("manifest_resource")

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def nickname(self) -> str | None:
        """Nickname."""
        return self.data.get("nickname_label")

    @property
    def name_unique(self) -> str | None:
        """Name unique."""
        if self.nickname:
            return f'{self.name} "{self.nickname}" ({self.city}, {self.region_name})'
        return f"{self.name} ({self.city}, {self.region_name})"

    @property
    def password(self) -> str | None:
        """Password."""
        return self.data.get("password")

    @property
    def pause_5g_enabled(self) -> bool | None:
        """Pause 5G enabled."""
        return self.data.get("temporary_flags", {}).get("hide_5g", {}).get("value")

    @property
    def pause_5g_expiration(self) -> str | None:
        """Pause 5G expiration."""
        return self.data.get("temporary_flags", {}).get("hide_5g", {}).get("expires_on")

    @pause_5g_enabled.setter
    def pause_5g_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        url = f"{self.url}/temporary_flags/hide_5g"
        if value:
            self.api.call(
                method=METHOD_PUT,
                url=url,
                json={
                    "value": True,
                },
            )
        else:
            self.api.call(
                method=METHOD_DELETE,
                url=url,
            )

    @property
    def postal_code(self) -> str | None:
        """Postal code."""
        return self.data.get("geo_ip", {}).get("postalCode")

    @property
    def preferred_update_hour(self) -> str | None:
        """Preferred update hour."""
        hour = self.data.get("updates", {}).get("preferred_update_hour")
        if hour is None:
            return hour
        return self.preferred_update_hour_options[
            list(PREFERRED_UPDATE_HOUR_MAP.values()).index(hour)
        ]

    @preferred_update_hour.setter
    def preferred_update_hour(self, value: str) -> None:
        if value not in self.preferred_update_hour_options:
            return
        self.api.call(
            method=METHOD_POST,
            url=f"/2.2/networks/{self.id}/updates/preferred_update_hour",
            json={
                "preferred_update_hour": PREFERRED_UPDATE_HOUR_MAP[value],
            },
        )

    @property
    def preferred_update_hour_options(self) -> list[str]:
        """Preferred update hour options."""
        return list(PREFERRED_UPDATE_HOUR_MAP.keys())

    @property
    def premium_capable(self) -> bool | None:
        """Premium capable."""
        return self.data.get("capabilities", {}).get("premium", {}).get("capable")

    @property
    def premium_status(self) -> str | None:
        """Premium status."""
        return self.data.get("premium_status")

    @property
    def premium_enabled(self) -> bool:
        """Premium enabled."""
        return premium_ok(
            capable=self.premium_capable,
            status=self.premium_status,
        )

    @property
    def public_ip(self) -> str | None:
        """Public IP."""
        return self.data.get("ip_settings", {}).get("public_ip")

    @property
    def qr_code(self) -> bytes | None:
        """QR code."""
        return generate_qr_code(
            ssid=self.ssid,
            password=self.password,
        )

    def reboot(self) -> None:
        """Reboot."""
        self.api.call(method=METHOD_POST, url=self.url_reboot)

    @property
    def region(self) -> str | None:
        """Region."""
        return self.data.get("geo_ip", {}).get("region")

    @property
    def region_name(self) -> str | None:
        """Region name."""
        return self.data.get("geo_ip", {}).get("regionName")

    def run_internet_backup_test(self) -> None:
        """Run internet backup test."""
        self.api.call(
            method=METHOD_POST,
            url=f"{self.url}/backup_access_points/connectivity_check",
        )

    def run_speed_test(self) -> None:
        """Run speed test."""
        self.api.call(method=METHOD_POST, url=f"{self.url}/speedtest")

    @property
    def speed_date(self) -> str | None:
        """Speed date."""
        return self.data.get("speed", {}).get("date")

    @property
    def speed_down(self) -> tuple[int | None, str | None]:
        """Speed down."""
        return (
            self.data.get("speed", {}).get("down", {}).get("value"),
            self.data.get("speed", {}).get("down", {}).get("units"),
        )

    @property
    def speed_up(self) -> tuple[int | None, str | None]:
        """Speed up."""
        return (
            self.data.get("speed", {}).get("up", {}).get("value"),
            self.data.get("speed", {}).get("up", {}).get("units"),
        )

    @property
    def sqm(self) -> bool | None:
        """SQM."""
        return self.data.get("sqm")

    @sqm.setter
    def sqm(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=self.url_settings,
            json={
                "sqm": value,
            },
        )

    @property
    def ssid(self) -> str | None:
        """SSID."""
        return self.name

    @property
    def status(self) -> str | None:
        """Status."""
        return self.data.get("status")

    @property
    def target_firmware(self) -> EeroFirmware:
        """Target firmware."""
        return EeroFirmware(
            self.data.get("updates", {}).get("release_notes", {}).get("target", {})
        )

    @property
    def thread_active_operational_dataset(self) -> str | None:
        """Thread active operational dataset."""
        return self.data.get("thread", {}).get("active_operational_dataset")

    @property
    def thread_channel(self) -> int | None:
        """Thread channel."""
        return self.data.get("thread", {}).get("channel")

    @property
    def thread_commissioning_credential(self) -> str | None:
        """Thread commissioning credentials."""
        return self.data.get("thread", {}).get("commissioning_credential")

    @property
    def thread_enabled(self) -> bool | None:
        """Thread enabled."""
        return self.data.get("thread", {}).get("enabled")

    @thread_enabled.setter
    def thread_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=f"{self.url_thread}/enable",
            json={
                "enabled": value,
            },
        )

    @property
    def thread_master_key(self) -> str | None:
        """Thread master key."""
        return self.data.get("thread", {}).get("master_key")

    @property
    def thread_name(self) -> str | None:
        """Thread name."""
        return self.data.get("thread", {}).get("name")

    @property
    def thread_pan_id(self) -> str | None:
        """Thread PAN ID."""
        return self.data.get("thread", {}).get("pan_id")

    @property
    def thread_xpan_id(self) -> str | None:
        """Thread XPAN ID."""
        return self.data.get("thread", {}).get("xpan_id")

    def update(self) -> None:
        """Update."""
        self.api.call(method=METHOD_POST, url=self.url_updates)

    @property
    def upnp(self) -> bool | None:
        """UPNP."""
        return self.data.get("upnp")

    @upnp.setter
    def upnp(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=self.url_settings,
            json={
                "upnp": value,
            },
        )

    @property
    def url_dns_policies(self) -> str:
        """URL DNS Policies."""
        return f"{self.url}/dns_policies"

    @property
    def url_insights(self) -> str | None:
        """URL insights."""
        return self.data.get("resources", {}).get("insights")

    @property
    def url_reboot(self) -> str | None:
        """URL reboot."""
        return self.data.get("resources", {}).get("reboot")

    @property
    def url_settings(self) -> str | None:
        """URL settings."""
        return self.data.get("resources", {}).get("settings")

    @property
    def url_thread(self) -> str | None:
        """URL thread."""
        return self.data.get("resources", {}).get("thread")

    @property
    def url_updates(self) -> str | None:
        """URL updates."""
        return self.data.get("resources", {}).get("updates")

    @property
    def wan_router_ip(self) -> str | None:
        """WAN router ip."""
        return self.data.get("lease", {}).get("dhcp", {}).get("router")

    @property
    def wan_subnet_mask(self) -> str | None:
        """WAN subnet mask."""
        return self.data.get("lease", {}).get("dhcp", {}).get("mask")

    @property
    def wpa3(self) -> bool | None:
        """WPA3."""
        return self.data.get("wpa3")

    @wpa3.setter
    def wpa3(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method=METHOD_PUT,
            url=self.url_settings,
            json={
                "wpa3": value,
            },
        )

    @property
    def backup_networks(self) -> list[EeroBackupNetwork | None]:
        """Backup networks."""
        return [
            EeroBackupNetwork(self.api, self, backup_network)
            for backup_network in self.data.get("backup_access_points", {}).get(
                "data", []
            )
        ]

    @property
    def clients(self) -> list[EeroClient | None]:
        """Clients."""
        return [
            EeroClient(self.api, self, client)
            for client in self.data.get("devices", {}).get("data", [])
        ]

    @property
    def eeros(self) -> list[EeroDevice | EeroDeviceBeacon | None]:
        """Eeros."""
        eeros = []
        for eero in self.data.get("eeros", {}).get("data", []):
            if eero["model"] == MODEL_BEACON:
                eeros.append(EeroDeviceBeacon(self.api, self, eero))
            else:
                eeros.append(EeroDevice(self.api, self, eero))
        return eeros

    @property
    def profiles(self) -> list[EeroProfile | None]:
        """Profiles."""
        return [
            EeroProfile(self.api, self, profile)
            for profile in self.data.get("profiles", {}).get("data", [])
        ]

    @property
    def resources(
        self,
    ) -> list[
        EeroBackupNetwork
        | EeroClient
        | EeroDevice
        | EeroDeviceBeacon
        | EeroProfile
        | None
    ]:
        """Resources."""
        return self.backup_networks + self.eeros + self.profiles + self.clients
