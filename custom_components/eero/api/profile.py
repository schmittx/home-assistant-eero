"""Eero API"""
from .resource import Resource


class Profile(Resource):

    def __init__(self, api, network, data):
        self.api = api
        self.network = network
        self.data = data

    @property
    def block_gaming_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_gaming_content")

    @block_gaming_content.setter
    def block_gaming_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_gaming_content=bool(value)),
        )

    @property
    def block_illegal_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_illegal_content")

    @block_illegal_content.setter
    def block_illegal_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_illegal_content=bool(value)),
        )

    @property
    def block_messaging_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_messaging_content")

    @block_messaging_content.setter
    def block_messaging_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_messaging_content=bool(value)),
        )

    @property
    def block_pornographic_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_pornographic_content")

    @block_pornographic_content.setter
    def block_pornographic_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_pornographic_content=bool(value)),
        )

    @property
    def block_shopping_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_shopping_content")

    @block_shopping_content.setter
    def block_shopping_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_shopping_content=bool(value)),
        )

    @property
    def block_social_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_social_content")

    @block_social_content.setter
    def block_social_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_social_content=bool(value)),
        )

    @property
    def block_streaming_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_streaming_content")

    @block_streaming_content.setter
    def block_streaming_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_streaming_content=bool(value)),
        )

    @property
    def block_violent_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_violent_content")

    @block_violent_content.setter
    def block_violent_content(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(block_violent_content=bool(value)),
        )

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
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("safe_search_enabled")

    @safe_search_enabled.setter
    def safe_search_enabled(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(safe_search_enabled=bool(value)),
        )

    @property
    def url_dns_policies(self):
        return f"{self.network.url}/dns_policies/profiles/{self.id}"

    @property
    def youtube_restricted(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("youtube_restricted")

    @youtube_restricted.setter
    def youtube_restricted(self, value):
        return self.api.post(
                url=self.url_dns_policies,
                json=dict(youtube_restricted=bool(value)),
        )
