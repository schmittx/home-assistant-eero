"""Eero API"""
from .resource import Resource

STATE_AMBIENT = "ambient"
STATE_DISABLED = "disabled"
STATE_SCHEDULE = "schedule"


class Eero(Resource):

    def _set_nightlight(self, json):
        return self.api.call(
            method="put",
            url=f"/2.2/eeros/{self.id}/nightlight/settings",
            json=json,
        )

    @property
    def connected_clients_count(self):
        return self.data.get("connected_clients_count")

    @property
    def data_usage_day(self):
        for eero in self.network.data.get("activity", {}).get("eeros", {}).get("data_usage_day", []):
            if eero["url"] == self.url:
                return (eero["download"], eero["upload"])
        return (None, None)

    @property
    def data_usage_month(self):
        for eero in self.network.data.get("activity", {}).get("eeros", {}).get("data_usage_month", []):
            if eero["url"] == self.url:
                return (eero["download"], eero["upload"])
        return (None, None)

    @property
    def data_usage_week(self):
        for eero in self.network.data.get("activity", {}).get("eeros", {}).get("data_usage_week", []):
            if eero["url"] == self.url:
                return (eero["download"], eero["upload"])
        return (None, None)

    @property
    def is_gateway(self):
        return self.data.get("gateway")

    @property
    def led_on(self):
        return self.data.get("led_on")

    @led_on.setter
    def led_on(self, value):
        self.api.call(
            method="put",
            url=self.url_led,
            json=dict(led_on=bool(value)),
        )

    @property
    def location(self):
        return self.data.get("location")

    @property
    def mac_address(self):
        return self.data.get("mac_address")

    @property
    def model(self):
        return self.data.get("model")

    @property
    def name(self):
        return self.location

    @property
    def name_long(self):
        return f"{self.name} Eero"

    @property
    def os_version(self):
        return self.data.get("os_version")

    def reboot(self):
        return self.api.call(method="post", url=self.url_reboot)

    @property
    def serial(self):
        return self.data.get("serial")

    @property
    def status(self):
        return self.data.get("status")

    @property
    def update_available(self):
        return self.data.get("update_available")

    @property
    def url_led(self):
        return self.data.get("resources", {}).get("led_action")

    @property
    def url_reboot(self):
        return self.data.get("resources", {}).get("reboot")


class EeroBeacon(Eero):

    @property
    def nightlight_brightness_percentage(self):
        return self.data.get("nightlight", {}).get("brightness_percentage")

    @property
    def nightlight_enabled(self):
        return self.data.get("nightlight", {}).get("enabled")

    @property
    def nightlight_schedule(self):
        return (
            self.data.get("nightlight", {}).get("schedule", {}).get("on"),
            self.data.get("nightlight", {}).get("schedule", {}).get("off"),
        )

    @property
    def nightlight_schedule_enabled(self):
        return self.data.get("nightlight", {}).get("schedule", {}).get("enabled")

    @property
    def nightlight_status(self):
        if not self.nightlight_enabled:
            return STATE_DISABLED
        elif not self.nightlight_schedule_enabled:
            return STATE_AMBIENT
        return STATE_SCHEDULE

    def set_nightlight_ambient(self):
        json = dict(enabled=True, schedule=dict(enabled=False))
        return self._set_nightlight(json)

    def set_nightlight_disabled(self):
        json = dict(enabled=False)
        return self._set_nightlight(json)

    def set_nightlight_schedule(self, time_on=None, time_off=None):
        if time_on is None:
            time_on = self.nightlight_schedule[0]
        if time_off is None:
            time_off = self.nightlight_schedule[1]
        json = dict(enabled=True, schedule=dict(enabled=True, on=time_on, off=time_off))
        return self._set_nightlight(json)
