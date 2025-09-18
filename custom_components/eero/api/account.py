"""Eero API."""

from __future__ import annotations

from .network import EeroNetwork
from .resource import EeroResource


class EeroAccount(EeroResource):
    """EeroAccount."""

    def __init__(self, api, data) -> None:
        """Initialize."""
        super().__init__(api=api, network=None, data=data)

    @property
    def email(self) -> str | None:
        """Email."""
        return self.data.get("email", {}).get("value")

    @property
    def log_id(self) -> str | None:
        """Log ID."""
        return self.data.get("log_id")

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def phone(self) -> str | None:
        """Phone."""
        return self.data.get("phone", {}).get("value")

    @property
    def premium_status(self) -> str | None:
        """Premium status."""
        return self.data.get("premium_status")

    @property
    def networks(self) -> list[EeroNetwork | None]:
        """Networks."""
        return [
            EeroNetwork(self.api, self, network)
            for network in self.data.get("networks", {}).get("data", [])
        ]
