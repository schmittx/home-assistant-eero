"""Eero API"""
from .const import URL_ACCOUNT


class Resource(object):

    def __init__(self, api, network, data):
        self.api = api
        self.network = network
        self.data = data

    @property
    def id(self):
        if self.is_network:
            return self.url.replace("/2.2/networks/", "")
        elif self.is_eero:
            return self.url.replace("/2.2/eeros/", "")
        elif self.is_profile:
            return self.url.replace(f"{self.network.url}/profiles/", "")
        elif self.is_client:
            return self.url.replace(f"{self.network.url}/devices/", "")
        return None

    @property
    def is_account(self):
        return bool(self.__class__.__name__ == "Account")

    @property
    def is_network(self):
        return bool(self.__class__.__name__ == "Network")

    @property
    def is_eero(self):
        return bool(self.__class__.__name__ in ["Eero", "EeroBeacon"])

    @property
    def is_eero_beacon(self):
        return bool(self.__class__.__name__ == "EeroBeacon")

    @property
    def is_profile(self):
        return bool(self.__class__.__name__ == "Profile")

    @property
    def is_client(self):
        return bool(self.__class__.__name__ == "Client")

    @property
    def url(self):
        if self.is_account:
            return URL_ACCOUNT
        return self.data.get("url")
