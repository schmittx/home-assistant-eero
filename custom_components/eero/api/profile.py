"""Eero API"""
from .resource import Resource


class Profile(Resource):

    def __init__(self, api, network, data):
        self.api = api
        self.network = network
        self.data = data

    @property
    def block_illegal_content(self):
        return self.data.get("premium_dns", {}).get("dns_policies", {}).get("block_illegal_content")

    @block_illegal_content.setter
    def block_illegal_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_illegal_content=bool(value)),
        )

    @property
    def block_pornographic_content(self):
        return self.data.get("premium_dns", {}).get("dns_policies", {}).get("block_pornographic_content")

    @block_pornographic_content.setter
    def block_pornographic_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_pornographic_content=bool(value)),
        )

    @property
    def block_violent_content(self):
        return self.data.get("premium_dns", {}).get("dns_policies", {}).get("block_violent_content")

    @block_violent_content.setter
    def block_violent_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_violent_content=bool(value)),
        )

    @property
    def id(self):
        return self.url.replace(f"/2.2/networks/{self.network.id}/profiles/", "")

    @property
    def name(self):
        return self.data.get("name")

    @property
    def name_long(self):
        return f"{self.name} Profile"

    @property
    def paused(self):
        return self.data.get("paused")

    @paused.setter
    def paused(self, value):
        self.api.put(
            url=self.url,
            json=dict(paused=bool(value)),
        )

    @property
    def safe_search_enabled(self):
        return self.data.get("premium_dns", {}).get("dns_policies", {}).get("safe_search_enabled")

    @safe_search_enabled.setter
    def safe_search_enabled(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(safe_search_enabled=bool(value)),
        )

    @property
    def url_dns_policies(self):
        return f"/2.2/networks/{self.network.id}/dns_policies/profiles/{self.id}"
