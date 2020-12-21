"""Eero API"""
from .const import URL_ACCOUNT


class Resource(object):

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
        return bool(self.__class__.__name__ == "Eero")

    @property
    def is_profile(self):
        return bool(self.__class__.__name__ == "Profile")

    @property
    def is_client(self):
        return bool(self.__class__.__name__ == "Client")

    @property
    def timezone(self):
        if self.is_network:
            return self.data.get("timezone", {}).get("value")
        elif any([self.is_eero, self.is_profile, self.is_client]):
            return self.network.timezone
        return None

    def update_data(self):
        self.data = self.api.get(url=self.url)

    @property
    def url(self):
        if self.is_account:
            return URL_ACCOUNT
        return self.data.get("url")

    @property
    def url_data_usage(self):
        if self.is_network:
            return f"{self.url}/data_usage"
        elif self.is_eero:
            return f"{self.network.url_data_usage}/eeros/{self.id}"
        elif self.is_profile:
            return f"{self.network.url_data_usage}/profiles/{self.id}"
        elif self.is_client:
            return f"{self.network.url_data_usage}/devices/{self.id}"
        return None

    @property
    def url_insights(self):
        if self.is_network:
            return self.data.get("resources", {}).get("insights")
        elif self.is_profile:
            return f"{self.network.url_insights}/profiles/{self.id}"
        elif self.is_client:
            return f"{self.network.url_insights}/devices/{self.id}"
        return None
