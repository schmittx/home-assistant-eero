"""Eero API"""
from __future__ import annotations

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
from .backup_network import EeroBackupNetwork
from .eero import EeroDevice, EeroDeviceBeacon
from .firmware import EeroFirmware
from .profile import EeroProfile
from .resource import EeroResource
from .util import generate_qr_code, premium_ok


class EeroNetwork(EeroResource):

    def __init__(self, api, account, data):
        super().__init__(api=api, network=None, data=data)
        self.account = account
        if self.data is None:
            self.data = {}

    @property
    def ad_block(self) -> bool:
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
        return self.data.get("premium_dns", {}).get("ad_block_settings", {}).get("enabled")

    @property
    def ad_block_profiles(self) -> list[str | None] | None:
        return self.data.get("premium_dns", {}).get("ad_block_settings", {}).get("profiles")

    @property
    def ad_block_status(self) -> str:
        if self.ad_block:
            return STATE_NETWORK
        elif self.ad_block_profiles:
            return STATE_PROFILE
        return STATE_DISABLED

    @property
    def adblock_day(self) -> int | None:
        for series in self.data.get("activity", {}).get("network", {}).get("adblock_day", []):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def adblock_month(self) -> int | None:
        for series in self.data.get("activity", {}).get("network", {}).get("adblock_month", []):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def adblock_week(self) -> int | None:
        for series in self.data.get("activity", {}).get("network", {}).get("adblock_week", []):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def backup_internet_enabled(self) -> bool | None:
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
        return self.data.get("premium_dns", {}).get("dns_policies", {}).get("block_malware")

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
        data={
            "blocked": None,
            "botnet": None,
            "domains": None,
            "malware": None,
            "parked": None,
            "phishing": None,
            "spyware": None,
        }
        for series in self.data.get("activity", {}).get("network", {}).get("blocked_day", []):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def blocked_month(self) -> dict[str, int | None]:
        data={
            "blocked": None,
            "botnet": None,
            "domains": None,
            "malware": None,
            "parked": None,
            "phishing": None,
            "spyware": None,
        }
        for series in self.data.get("activity", {}).get("network", {}).get("blocked_month", []):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def blocked_week(self) -> dict[str, int | None]:
        data={
            "blocked": None,
            "botnet": None,
            "domains": None,
            "malware": None,
            "parked": None,
            "phishing": None,
            "spyware": None,
        }
        for series in self.data.get("activity", {}).get("network", {}).get("blocked_week", []):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def city(self) -> str | None:
        return self.data.get("geo_ip", {}).get("city")

    @property
    def clients_count(self) -> int | None:
        return self.data.get("clients", {}).get("count")

    @property
    def connected_clients_count(self) -> int:
        return len([client for client in self.clients if client.connected])

    @property
    def connected_clients_count_computers_personal(self) -> int:
        return len([client for client in self.clients if client.connected and client.device_category == DEVICE_CATEGORY_COMPUTERS_PERSONAL])

    @property
    def connected_clients_count_entertainment(self) -> int:
        return len([client for client in self.clients if client.connected and client.device_category == DEVICE_CATEGORY_ENTERTAINMENT])

    @property
    def connected_clients_count_home(self) -> int:
        return len([client for client in self.clients if client.connected and client.device_category == DEVICE_CATEGORY_HOME])

    @property
    def connected_clients_count_other(self) -> int:
        return len([client for client in self.clients if client.connected and client.device_category == DEVICE_CATEGORY_OTHER])

    @property
    def connected_guest_clients_count(self) -> int:
        return len([client for client in self.clients if client.connected and client.is_guest])

    @property
    def connected_guest_clients_count_computers_personal(self) -> int:
        return len([client for client in self.clients if client.connected and client.is_guest and client.device_category == DEVICE_CATEGORY_COMPUTERS_PERSONAL])

    @property
    def connected_guest_clients_count_entertainment(self) -> int:
        return len([client for client in self.clients if client.connected and client.is_guest and client.device_category == DEVICE_CATEGORY_ENTERTAINMENT])

    @property
    def connected_guest_clients_count_home(self) -> int:
        return len([client for client in self.clients if client.connected and client.is_guest and client.device_category == DEVICE_CATEGORY_HOME])

    @property
    def connected_guest_clients_count_other(self) -> int:
        return len([client for client in self.clients if client.connected and client.is_guest and client.device_category == DEVICE_CATEGORY_OTHER])

    @property
    def country_code(self) -> str | None:
        return self.data.get("geo_ip", {}).get("countryCode")

    @property
    def country_name(self) -> str | None:
        return self.data.get("geo_ip", {}).get("countryName")

    @property
    def data_usage_day(self) -> tuple[int | None, int | None]:
        down, up = None, None
        for series in self.data.get("activity", {}).get("network", {}).get("data_usage_day", []):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def data_usage_month(self) -> tuple[int | None, int | None]:
        down, up = None, None
        for series in self.data.get("activity", {}).get("network", {}).get("data_usage_month", []):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def data_usage_week(self) -> tuple[int | None, int | None]:
        down, up = None, None
        for series in self.data.get("activity", {}).get("network", {}).get("data_usage_week", []):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def ddns_enabled(self) -> bool | None:
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
        return self.data.get("ddns", {}).get("subdomain")

    @property
    def dns_caching(self) -> bool | None:
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
        return [EeroFirmware(firmware) for firmware in self.data.get("updates", {}).get("release_notes", {}).get("history", [])]

    @property
    def gateway_mac_address(self) -> str | None:
        for eero in self.eeros:
            if eero.is_gateway:
                return eero.mac_address
        return None

    @property
    def gateway_name(self) -> str | None:
        for eero in self.eeros:
            if eero.is_gateway:
                return eero.name
        return None

    @property
    def guest_network_enabled(self) -> bool | None:
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
        return self.data.get("guest_network", {}).get("name")

    @property
    def guest_network_password(self) -> str | None:
        return self.data.get("guest_network", {}).get("password")

    @property
    def guest_network_qr_code(self) -> bytes | None:
        if all(
            [
                not self.guest_network_enabled,
                self.api.default_qr_code,
            ]
        ):
            return self.api.default_qr_code
        return generate_qr_code(
            ssid=self.guest_network_name,
            password=self.guest_network_password,
        )

    @property
    def health_eero_network_status(self) -> str | None:
        return self.data.get("health", {}).get("eero_network", {}).get("status")

    @property
    def health_internet_isp_up(self) -> bool | None:
        return self.data.get("health", {}).get("internet", {}).get("isp_up")

    @property
    def health_internet_status(self) -> str | None:
        return self.data.get("health", {}).get("internet", {}).get("status")

    @property
    def inspected_day(self) -> int | None:
        for series in self.data.get("activity", {}).get("network", {}).get("inspected_day", []):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def inspected_month(self) -> int | None:
        for series in self.data.get("activity", {}).get("network", {}).get("inspected_month", []):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def inspected_week(self) -> int | None:
        for series in self.data.get("activity", {}).get("network", {}).get("inspected_week", []):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def ipv6_upstream(self) -> bool | None:
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
        return self.data.get("geo_ip", {}).get("isp")

    @property
    def manifest_resource(self) -> str | None:
        return self.data.get("updates", {}).get("manifest_resource")

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def nickname(self) -> str | None:
        return self.data.get("nickname_label")

    @property
    def name_unique(self) -> str | None:
        if self.nickname:
            return f'{self.name} "{self.nickname}" ({self.city}, {self.region_name})'
        return f"{self.name} ({self.city}, {self.region_name})"

    @property
    def password(self) -> str | None:
        return self.data.get("password")

    @property
    def pause_5g_enabled(self) -> bool | None:
        return self.data.get("temporary_flags", {}).get("hide_5g", {}).get("value")

    @property
    def pause_5g_expiration(self) -> str | None:
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
    def public_ip(self) -> str | None:
        return self.data.get("ip_settings", {}).get("public_ip")

    @property
    def postal_code(self) -> str | None:
        return self.data.get("geo_ip", {}).get("postalCode")

    @property
    def preferred_update_hour(self) -> str | None:
        hour = self.data.get("updates", {}).get("preferred_update_hour")
        if hour is None:
            return hour
        return self.preferred_update_hour_options[list(PREFERRED_UPDATE_HOUR_MAP.values()).index(hour)]

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
        return list(PREFERRED_UPDATE_HOUR_MAP.keys())

    @property
    def premium_capable(self) -> bool | None:
        return self.data.get("capabilities", {}).get("premium", {}).get("capable")

    @property
    def premium_status(self) -> str | None:
        return self.data.get("premium_status")

    @property
    def premium_enabled(self) -> bool:
        return premium_ok(
            capable=self.premium_capable,
            status=self.premium_status,
        )

    @property
    def qr_code(self) -> bytes | None:
        return generate_qr_code(
            ssid=self.ssid,
            password=self.password,
        )

    def reboot(self) -> None:
        self.api.call(method=METHOD_POST, url=self.url_reboot)

    @property
    def region(self) -> str | None:
        return self.data.get("geo_ip", {}).get("region")

    @property
    def region_name(self) -> str | None:
        return self.data.get("geo_ip", {}).get("regionName")

    def run_speed_test(self) -> None:
        self.api.call(method=METHOD_POST, url=f"{self.url}/speedtest")

    @property
    def speed_date(self) -> str | None:
        return self.data.get("speed", {}).get("date")

    @property
    def speed_down(self) -> tuple[int | None, str | None]:
        return (
            self.data.get("speed", {}).get("down", {}).get("value"),
            self.data.get("speed", {}).get("down", {}).get("units"),
        )

    @property
    def speed_up(self) -> tuple[int | None, str | None]:
        return (
            self.data.get("speed", {}).get("up", {}).get("value"),
            self.data.get("speed", {}).get("up", {}).get("units"),
        )

    @property
    def sqm(self) -> bool | None:
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
        return self.name

    @property
    def status(self) -> str | None:
        return self.data.get("status")

    @property
    def target_firmware(self) -> EeroFirmware:
        return EeroFirmware(self.data.get("updates", {}).get("release_notes", {}).get("target", {}))

    @property
    def thread_active_operational_dataset(self) -> str | None:
        return self.data.get("thread", {}).get("active_operational_dataset")

    @property
    def thread_channel(self) -> int | None:
        return self.data.get("thread", {}).get("channel")

    @property
    def thread_commissioning_credential(self) -> str | None:
        return self.data.get("thread", {}).get("commissioning_credential")

    @property
    def thread_enabled(self) -> bool | None:
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
        return self.data.get("thread", {}).get("master_key")

    @property
    def thread_name(self) -> str | None:
        return self.data.get("thread", {}).get("name")

    @property
    def thread_pan_id(self) -> str | None:
        return self.data.get("thread", {}).get("pan_id")

    @property
    def thread_xpan_id(self) -> str | None:
        return self.data.get("thread", {}).get("xpan_id")

    def update(self) -> None:
        self.api.call(method=METHOD_POST, url=self.url_updates)

    @property
    def upnp(self) -> bool | None:
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
        return f"{self.url}/dns_policies"

    @property
    def url_insights(self) -> str | None:
        return self.data.get("resources", {}).get("insights")

    @property
    def url_reboot(self) -> str | None:
        return self.data.get("resources", {}).get("reboot")

    @property
    def url_settings(self) -> str | None:
        return self.data.get("resources", {}).get("settings")

    @property
    def url_thread(self) -> str | None:
        return self.data.get("resources", {}).get("thread")

    @property
    def url_updates(self) -> str | None:
        return self.data.get("resources", {}).get("updates")

    @property
    def wpa3(self) -> bool | None:
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
        backup_networks = []
        for backup_network in self.data.get("backup_access_points", {}).get("data", []):
            backup_networks.append(EeroBackupNetwork(self.api, self, backup_network))
        return backup_networks

    @property
    def clients(self) -> list[EeroClient | None]:
        clients = []
        for client in self.data.get("devices", {}).get("data", []):
            clients.append(EeroClient(self.api, self, client))
        return clients

    @property
    def eeros(self) -> list[EeroDevice | EeroDeviceBeacon | None]:
        eeros = []
        for eero in self.data.get("eeros", {}).get("data", []):
            if eero["model"] == MODEL_BEACON:
                eeros.append(EeroDeviceBeacon(self.api, self, eero))
            else:
                eeros.append(EeroDevice(self.api, self, eero))
        return eeros

    @property
    def profiles(self) -> list[EeroProfile | None]:
        profiles = []
        for profile in self.data.get("profiles", {}).get("data", []):
            profiles.append(EeroProfile(self.api, self, profile))
        return profiles

    @property
    def resources(self) -> list[EeroBackupNetwork | EeroClient | EeroDevice | EeroDeviceBeacon | EeroProfile | None]:
        return self.backup_networks + self.eeros + self.profiles + self.clients
