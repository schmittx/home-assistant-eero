"""Eero API"""
from .client import Client
from .resource import Resource


class Profile(Resource):

    @property
    def ad_block(self):
        return all(
            [
                self.network.ad_block_enabled,
                self.url in self.network.ad_block_profiles,
            ]
        )

    @ad_block.setter
    def ad_block(self, value):
        enable = bool(value)
        profiles = self.network.ad_block_profiles
        if value:
            profiles.append(self.url)
        else:
            profiles.remove(self.url)
            if profiles:
                enable = True

        return self.api.call(
            method="post",
            url=f"{self.network.url_dns_policies}/adblock",
            json=dict(enable=enable, profiles=profiles),
        )

    @property
    def adblock_day(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("adblock_day", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def adblock_month(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("adblock_month", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def adblock_week(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("adblock_week", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def block_apps_enabled(self):
        return bool(self.blocked_applications)

    @property
    def block_gaming_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_gaming_content")

    @block_gaming_content.setter
    def block_gaming_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_gaming_content=bool(value)),
        )

    @property
    def block_illegal_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_illegal_content")

    @block_illegal_content.setter
    def block_illegal_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_illegal_content=bool(value)),
        )

    @property
    def block_messaging_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_messaging_content")

    @block_messaging_content.setter
    def block_messaging_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_messaging_content=bool(value)),
        )

    @property
    def block_pornographic_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_pornographic_content")

    @block_pornographic_content.setter
    def block_pornographic_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_pornographic_content=bool(value)),
        )

    @property
    def block_shopping_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_shopping_content")

    @block_shopping_content.setter
    def block_shopping_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_shopping_content=bool(value)),
        )

    @property
    def block_social_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_social_content")

    @block_social_content.setter
    def block_social_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_social_content=bool(value)),
        )

    @property
    def block_streaming_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_streaming_content")

    @block_streaming_content.setter
    def block_streaming_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_streaming_content=bool(value)),
        )

    @property
    def block_violent_content(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("block_violent_content")

    @block_violent_content.setter
    def block_violent_content(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(block_violent_content=bool(value)),
        )

    @property
    def blocked_applications(self):
        return self.data.get("premium_dns", {}).get("blocked_applications")

    def set_blocked_applications(self, blocked_applications):
        return self.api.call(
            method="put",
            url=f"{self.url_dns_policies}/applications/blocked",
            json=dict(applications=blocked_applications),
        )

    @property
    def blocked_day(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("blocked_day", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def blocked_month(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("blocked_month", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def blocked_week(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("blocked_week", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def connected(self):
        return bool(self.connected_clients_count != 0)

    @property
    def connected_clients_count(self):
        return len([client for client in self.clients if client.connected])

    @property
    def data_usage_day(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("data_usage_day", []):
            if str(profile["profile_id"]) == self.id:
                return (profile["download"], profile["upload"])
        return (None, None)

    @property
    def data_usage_month(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("data_usage_month", []):
            if str(profile["profile_id"]) == self.id:
                return (profile["download"], profile["upload"])
        return (None, None)

    @property
    def data_usage_week(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("data_usage_week", []):
            if str(profile["profile_id"]) == self.id:
                return (profile["download"], profile["upload"])
        return (None, None)

    @property
    def inspected_day(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("inspected_day", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def inspected_month(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("inspected_month", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

    @property
    def inspected_week(self):
        for profile in self.network.data.get("activity", {}).get("profiles", {}).get("inspected_week", []):
            if profile["insights_url"] == self.url_insights:
                return profile["sum"]
        return None

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
        self.api.call(
            method="put",
            url=self.url,
            json=dict(paused=bool(value)),
        )

    @property
    def safe_search_enabled(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("safe_search_enabled")

    @safe_search_enabled.setter
    def safe_search_enabled(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(safe_search_enabled=bool(value)),
        )

    @property
    def url_dns_policies(self):
        return f"{self.network.url}/dns_policies/profiles/{self.id}"

    @property
    def url_insights(self):
        return f"{self.network.url_insights}/profiles/{self.id}"

    @property
    def youtube_restricted(self):
        return self.data.get("unified_content_filters", {}).get("dns_policies", {}).get("youtube_restricted")

    @youtube_restricted.setter
    def youtube_restricted(self, value):
        return self.api.call(
            method="post",
            url=self.url_dns_policies,
            json=dict(youtube_restricted=bool(value)),
        )

    @property
    def clients(self):
        clients = []
        for client in self.data.get("devices", []):
            clients.append(Client(self.api, self, client))
        return clients
