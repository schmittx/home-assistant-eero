"""Eero API"""
from .resource import Resource


class Client(Resource):

    @property
    def adblock_day(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_month(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_week(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_day(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_month(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_week(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_day(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_month(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def adblock_week(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("adblock_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_day(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_month(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def blocked_week(self):
        for device in self.network.data.get("activity", {}).get("network", {}).get("blocked_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None
    @property
    def connected(self):
        return self.data.get("connected")

    @property
    def connection_type(self):
        return self.data.get("connection_type")

    @property
    def data_usage_day(self):
        for device in self.network.data.get("activity", {}).get("devices", {}).get("data_usage_day", []):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def data_usage_month(self):
        for device in self.network.data.get("activity", {}).get("devices", {}).get("data_usage_month", []):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def data_usage_week(self):
        for device in self.network.data.get("activity", {}).get("devices", {}).get("data_usage_week", []):
            if device["url"] == self.url:
                return (device["download"], device["upload"])
        return (None, None)

    @property
    def device_type(self):
        return self.data.get("device_type")

    @property
    def hostname(self):
        return self.data.get("hostname")

    @property
    def inspected_day(self):
        for device in self.network.data.get("activity", {}).get("devices", {}).get("inspected_day", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def inspected_month(self):
        for device in self.network.data.get("activity", {}).get("devices", {}).get("inspected_month", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def inspected_week(self):
        for device in self.network.data.get("activity", {}).get("devices", {}).get("inspected_week", []):
            if device["insights_url"] == self.url_insights:
                return device["sum"]
        return None

    @property
    def ip(self):
        return self.data.get("ip")

    @property
    def is_guest(self):
        return self.data.get("is_guest")

    @property
    def is_private(self):
        return self.data.get("is_private")

    @property
    def mac(self):
        return self.data.get("mac")

    @property
    def manufacturer(self):
        return self.data.get("manufacturer")

    @property
    def name(self):
        if self.nickname:
            return self.nickname
        elif self.hostname:
            return self.hostname
        return self.mac

    @property
    def name_connection_type(self):
        return f"{self.name} ({self.connection_type.title()})"

    @property
    def name_mac(self):
        return f"{self.name} ({self.mac})"

    @property
    def nickname(self):
        return self.data.get("nickname")

    @property
    def paused(self):
        return self.data.get("paused")

    @paused.setter
    def paused(self, value):
        return self.api.call(
            method="put",
            url=self.url,
            json=dict(paused=bool(value)),
        )
    @property
    def source_location(self):
        return self.data.get("source", {}).get("location")

    @property
    def url_insights(self):
        return f"{self.network.url_insights}/devices/{self.id}"

    @property
    def wireless(self):
        return self.data.get("wireless")
