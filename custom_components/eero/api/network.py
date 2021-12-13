"""Eero API"""
from .client import Client
from .const import MODEL_BEACON, PERIOD_DAY, PERIOD_WEEK, PERIOD_MONTH
from .eero import Eero, EeroBeacon
from .profile import Profile
from .resource import Resource

STATE_DISABLED = "disabled"
STATE_NETWORK = "network"
STATE_PROFILES = "profiles"


class Network(Resource):

    def __init__(self, api, account, data):
        super().__init__(api=api, network=None, data=data)
        self.account = account

    @property
    def ad_block(self):
        return all(
            [
                self.ad_block_enabled,
                not self.ad_block_profiles,
            ]
        )

    @ad_block.setter
    def ad_block(self, value):
        return self.api.call(
            method="post",
            url=f"{self.url_dns_policies}/adblock",
            json=dict(enable=bool(value)),
        )

    @property
    def ad_block_enabled(self):
        return self.data.get("premium_dns", {}).get("ad_block_settings", {}).get("enabled")

    @property
    def ad_block_profiles(self):
        return self.data.get("premium_dns", {}).get("ad_block_settings", {}).get("profiles")

    @property
    def ad_block_status(self):
        if self.ad_block:
            return STATE_NETWORK
        elif self.ad_block_profiles:
            return STATE_PROFILES
        return STATE_DISABLED

    @property
    def adblock_day(self):
        for series in self.data.get("activity", {}).get("network", {}).get("adblock_day", []):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def adblock_month(self):
        for series in self.data.get("activity", {}).get("network", {}).get("adblock_month", []):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def adblock_week(self):
        for series in self.data.get("activity", {}).get("network", {}).get("adblock_week", []):
            if series["insight_type"] == "adblock":
                return series["sum"]
        return None

    @property
    def band_steering(self):
        return self.data.get("band_steering")

    @band_steering.setter
    def band_steering(self, value):
        return self.api.call(
            method="put",
            url=self.url_settings,
            json=dict(band_steering=bool(value)),
        )

    @property
    def block_malware(self):
        return self.data.get("premium_dns", {}).get("dns_policies", {}).get("block_malware")

    @block_malware.setter
    def block_malware(self, value):
        return self.api.call(
            method="post",
            url=f"{self.url_dns_policies}/network",
            json=dict(block_malware=bool(value)),
        )

    @property
    def blocked_day(self):
        data=dict(blocked=None, botnet=None, domains=None, malware=None, parked=None, phishing=None, spyware=None)
        for series in self.data.get("activity", {}).get("network", {}).get("blocked_day", []):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def blocked_month(self):
        data=dict(blocked=None, botnet=None, domains=None, malware=None, parked=None, phishing=None, spyware=None)
        for series in self.data.get("activity", {}).get("network", {}).get("blocked_month", []):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def blocked_week(self):
        data=dict(blocked=None, botnet=None, domains=None, malware=None, parked=None, phishing=None, spyware=None)
        for series in self.data.get("activity", {}).get("network", {}).get("blocked_week", []):
            if series["insight_type"] in list(data.keys()):
                data[series["insight_type"]] = series["sum"]
        return data

    @property
    def city(self):
        return self.data.get("geo_ip", {}).get("city")

    @property
    def clients_count(self):
        return self.data.get("clients", {}).get("count")

    @property
    def connected_clients_count(self):
        return len([client for client in self.clients if client.connected])

    @property
    def connected_guest_clients_count(self):
        return len([client for client in self.clients if client.connected and client.is_guest])

    @property
    def country_code(self):
        return self.data.get("geo_ip", {}).get("countryCode")

    @property
    def country_name(self):
        return self.data.get("geo_ip", {}).get("countryName")

    @property
    def data_usage_day(self):
        down, up = None, None
        for series in self.data.get("activity", {}).get("network", {}).get("data_usage_day", []):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def data_usage_month(self):
        down, up = None, None
        for series in self.data.get("activity", {}).get("network", {}).get("data_usage_month", []):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def data_usage_week(self):
        down, up = None, None
        for series in self.data.get("activity", {}).get("network", {}).get("data_usage_week", []):
            if series["type"] == "download":
                down = series["sum"]
            elif series["type"] == "upload":
                up = series["sum"]
        return (down, up)

    @property
    def ddns_enabled(self):
        return self.data.get("ddns", {}).get("enabled")

    @ddns_enabled.setter
    def ddns_enabled(self, value):
        target = "enable" if value else "disable"
        return self.api.call(
            method="put",
            url=f"/2.2/networks/{self.id}/ddns/{target}",
        )

    @property
    def ddns_subdomain(self):
        return self.data.get("ddns", {}).get("subdomain")

    @property
    def dns_caching(self):
        return self.data.get("dns", {}).get("caching")

    @dns_caching.setter
    def dns_caching(self, value):
        return self.api.call(
            method="put",
            url=f"/2.2/networks/{self.id}/dns",
            json=dict(caching=bool(value)),
        )

    @property
    def gateway_mac_address(self):
        for eero in self.eeros:
            if eero.is_gateway:
                return eero.mac_address
        return None

    @property
    def gateway_name(self):
        for eero in self.eeros:
            if eero.is_gateway:
                return eero.name
        return None

    @property
    def guest_connected(self):
        return bool(self.connected_guest_clients_count != 0)

    @property
    def guest_network_enabled(self):
        return self.data.get("guest_network", {}).get("enabled")

    @guest_network_enabled.setter
    def guest_network_enabled(self, value):
        return self.api.call(
            method="put",
            url=f"/2.2/networks/{self.id}/guestnetwork",
            json=dict(enabled=bool(value)),
        )

    @property
    def guest_network_name(self):
        return self.data.get("guest_network", {}).get("name")

    @property
    def guest_network_password(self):
        return self.data.get("guest_network", {}).get("password")

    @property
    def health_eero_network_status(self):
        return self.data.get("health", {}).get("eero_network", {}).get("status")

    @property
    def health_internet_isp_up(self):
        return self.data.get("health", {}).get("internet", {}).get("isp_up")

    @property
    def health_internet_status(self):
        return self.data.get("health", {}).get("internet", {}).get("status")

    @property
    def inspected_day(self):
        for series in self.data.get("activity", {}).get("network", {}).get("inspected_day", []):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def inspected_month(self):
        for series in self.data.get("activity", {}).get("network", {}).get("inspected_month", []):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def inspected_week(self):
        for series in self.data.get("activity", {}).get("network", {}).get("inspected_week", []):
            if series["insight_type"] == "inspected":
                return series["sum"]
        return None

    @property
    def ipv6_upstream(self):
        return self.data.get("ipv6_upstream")

    @ipv6_upstream.setter
    def ipv6_upstream(self, value):
        return self.api.call(
            method="put",
            url=self.url_settings,
            json=dict(ipv6_upstream=bool(value)),
        )

    @property
    def isp(self):
        return self.data.get("geo_ip", {}).get("isp")

    @property
    def name(self):
        return self.data.get("name")

    @property
    def name_long(self):
        network_names = [network.name for network in self.account.networks]
        if network_names.count(self.name) > 1:
            return f"{self.name} ({self.city, self.region_name})"
        return self.name

    @property
    def password(self):
        return self.data.get("password")

    @property
    def public_ip(self):
        return self.data.get("ip_settings", {}).get("public_ip")

    @property
    def postal_code(self):
        return self.data.get("geo_ip", {}).get("postalCode")

    @property
    def premium_status(self):
        return self.data.get("premium_status")

    @property
    def premium_status_active(self):
        return bool(self.premium_status == "active")

    def reboot(self):
        return self.api.call(method="post", url=self.url_reboot)

    @property
    def region(self):
        return self.data.get("geo_ip", {}).get("region")

    @property
    def region_name(self):
        return self.data.get("geo_ip", {}).get("regionName")

    @property
    def speed_date(self):
        return self.data.get("speed", {}).get("date")

    @property
    def speed_down(self):
        return (
            self.data.get("speed", {}).get("down", {}).get("value"),
            self.data.get("speed", {}).get("down", {}).get("units"),
        )

    @property
    def speed_up(self):
        return (
            self.data.get("speed", {}).get("up", {}).get("value"),
            self.data.get("speed", {}).get("up", {}).get("units"),
        )

    @property
    def sqm(self):
        return self.data.get("sqm")

    @sqm.setter
    def sqm(self, value):
        return self.api.call(
            method="put",
            url=self.url_settings,
            json=dict(sqm=bool(value)),
        )

    @property
    def ssid(self):
        return self.name

    @property
    def status(self):
        return self.data.get("status")

    @property
    def target_firmware(self):
        return self.data.get("updates", {}).get("target_firmware")

    @property
    def thread(self):
        return self.data.get("thread")

    @thread.setter
    def thread(self, value):
        return self.api.call(
            method="put",
            url=self.url_settings,
            json=dict(thread=bool(value)),
        )

    @property
    def update_available(self):
        return self.data.get("updates", {}).get("can_update_now")

    @property
    def upnp(self):
        return self.data.get("upnp")

    @upnp.setter
    def upnp(self, value):
        return self.api.call(
            method="put",
            url=self.url_settings,
            json=dict(upnp=bool(value)),
        )

    @property
    def url_dns_policies(self):
        return f"{self.url}/dns_policies"

    @property
    def url_insights(self):
        return self.data.get("resources", {}).get("insights")

    @property
    def url_reboot(self):
        return self.data.get("resources", {}).get("reboot")

    @property
    def url_settings(self):
        return self.data.get("resources", {}).get("settings")

    @property
    def wpa3(self):
        return self.data.get("wpa3")

    @wpa3.setter
    def wpa3(self, value):
        return self.api.call(
            method="put",
            url=self.url_settings,
            json=dict(wpa3=bool(value)),
        )

    @property
    def eeros(self):
        eeros = []
        for eero in self.data.get("eeros", {}).get("data", []):
            if eero["model"] == MODEL_BEACON:
                eeros.append(EeroBeacon(self.api, self, eero))
            else:
                eeros.append(Eero(self.api, self, eero))
        return eeros

    @property
    def profiles(self):
        profiles = []
        for profile in self.data.get("profiles", {}).get("data", []):
            profiles.append(Profile(self.api, self, profile))
        return profiles

    @property
    def clients(self):
        clients = []
        for client in self.data.get("devices", {}).get("data", []):
            clients.append(Client(self.api, self, client))
        return clients

    @property
    def resources(self):
        return self.eeros + self.profiles + self.clients
