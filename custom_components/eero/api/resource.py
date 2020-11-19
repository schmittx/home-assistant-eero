"""Eero API"""
from .const import URL_ACCOUNT


class Resource(object):

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
    def url(self):
        if self.is_account:
            return URL_ACCOUNT
        return self.data.get("url")

    def update_data(self):
        self.data = self.api.get(url=self.url)
