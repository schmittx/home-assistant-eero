"""Eero API"""
from .resource import Resource


class Client(Resource):

    def __init__(self, api, network, data):
        self.api = api
        self.network = network
        self.data = data

    @property
    def connected(self):
        return self.data.get("connected")

    @property
    def connection_type(self):
        return self.data.get("connection_type")

    @property
    def device_type(self):
        return self.data.get("device_type")

    @property
    def hostname(self):
        return self.data.get("hostname")

    @property
    def id(self):
        return self.url.replace(f"/2.2/networks/{self.network.id}/devices/", "")

    @property
    def ip(self):
        return self.data.get("ip")

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
        return self.api.put(
                url=self.url,
                json=dict(paused=bool(value)),
        )
    @property
    def source_location(self):
        return self.data.get("source", {}).get("location")

    @property
    def wireless(self):
        return self.data.get("wireless")
