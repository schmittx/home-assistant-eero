"""Eero API"""
from .network import Network
from .resource import Resource


class Account(Resource):

    def __init__(self, api, data):
        super().__init__(api=api, network=None, data=data)

    @property
    def email(self):
        return self.data.get("email", {}).get("value")

    @property
    def log_id(self):
        return self.data.get("log_id")

    @property
    def name(self):
        return self.data.get("name")

    @property
    def phone(self):
        return self.data.get("phone", {}).get("value")

    @property
    def premium_status(self):
        return self.data.get("premium_status")

    @property
    def networks(self):
        networks = []
        for network in self.data.get("networks", {}).get("data", []):
            networks.append(Network(self.api, self, network))
        return networks
