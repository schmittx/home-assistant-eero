"""Eero API"""
from __future__ import annotations

from .const import STATE_AMBIENT, STATE_DISABLED, STATE_SCHEDULE
from .resource import EeroResource


class EeroDevice(EeroResource):

    @property
    def connected_clients_count(self) -> int | None:
        return self.data.get("connected_clients_count")

    @property
    def data_usage_day(self) -> tuple[int | None, int | None]:
        for eero in self.network.data.get("activity", {}).get("eeros", {}).get("data_usage_day", []):
            if eero["url"] == self.url:
                return (eero["download"], eero["upload"])
        return (None, None)

    @property
    def data_usage_month(self) -> tuple[int | None, int | None]:
        for eero in self.network.data.get("activity", {}).get("eeros", {}).get("data_usage_month", []):
            if eero["url"] == self.url:
                return (eero["download"], eero["upload"])
        return (None, None)

    @property
    def data_usage_week(self) -> tuple[int | None, int | None]:
        for eero in self.network.data.get("activity", {}).get("eeros", {}).get("data_usage_week", []):
            if eero["url"] == self.url:
                return (eero["download"], eero["upload"])
        return (None, None)

    @property
    def is_gateway(self) -> bool | None:
        return self.data.get("gateway")

    @property
    def status_light_brightness(self) -> int | None:
        return self.data.get("led_brightness")

    @property
    def status_light_enabled(self) -> bool | None:
        return self.data.get("led_on")

    def set_status_light_brightness(self, value: int) -> None:
        if not isinstance(value, int):
            return
        elif not value:
            self.set_status_light_off
            return
        self.api.call(
            method="put",
            url=self.url_led,
            json=dict(led_brightness=value),
        )

    def set_status_light(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=self.url_led,
            json=dict(led_on=value),
        )

    def set_status_light_off(self) -> None:
        self.set_status_light(value=False)

    def set_status_light_on(self) -> None:
        self.set_status_light(value=True)

    @property
    def location(self) -> str | None:
        return self.data.get("location")

    @property
    def mac_address(self) -> str | None:
        return self.data.get("mac_address")

    @property
    def model(self) -> str | None:
        return self.data.get("model")

    @property
    def model_number(self) -> str | None:
        return self.data.get("model_number")

    @property
    def name(self) -> str | None:
        return self.location

    @property
    def name_long(self) -> str:
        return f"{self.name} Eero"

    @property
    def os_version(self) -> str | None:
        return self.data.get("os_version")

    def reboot(self) -> None:
        self.api.call(method="post", url=self.url_reboot)

    @property
    def serial(self) -> str | None:
        return self.data.get("serial")

    @property
    def status(self) -> str | None:
        return self.data.get("status")

    @property
    def update_available(self) -> bool | None:
        return self.data.get("update_available")

    @property
    def url_led(self) -> str | None:
        return self.data.get("resources", {}).get("led_action")

    @property
    def url_reboot(self) -> str | None:
        return self.data.get("resources", {}).get("reboot")


class EeroDeviceBeacon(EeroDevice):

    @property
    def nightlight_brightness_percentage(self) -> int | None:
        return self.data.get("nightlight", {}).get("brightness_percentage")

    @nightlight_brightness_percentage.setter
    def nightlight_brightness_percentage(self, value: int) -> None:
        if not isinstance(value, int):
            return
        self.set_nightlight_brightness(value=value)

    @property
    def nightlight_enabled(self) -> bool | None:
        return self.data.get("nightlight", {}).get("enabled")

    @property
    def nightlight_mode(self) -> str:
        if not self.nightlight_enabled:
            return STATE_DISABLED
        elif not self.nightlight_schedule_enabled:
            return STATE_AMBIENT
        return STATE_SCHEDULE

    @nightlight_mode.setter
    def nightlight_mode(self, value: str) -> None:
        if value == STATE_DISABLED:
            self.set_nightlight_disabled()
        if value == STATE_AMBIENT:
            self.set_nightlight_ambient()
        if value == STATE_SCHEDULE:
            self.set_nightlight_schedule()

    @property
    def nightlight_mode_options(self) -> list[str]:
        return [STATE_AMBIENT, STATE_DISABLED, STATE_SCHEDULE]

    @property
    def nightlight_schedule(self) -> tuple[str | None, str | None]:
        return (
            self.data.get("nightlight", {}).get("schedule", {}).get("on"),
            self.data.get("nightlight", {}).get("schedule", {}).get("off"),
        )

    @property
    def nightlight_schedule_enabled(self) -> bool | None:
        return self.data.get("nightlight", {}).get("schedule", {}).get("enabled")

    def _set_nightlight(self, json: dict) -> None:
        if not isinstance(json, dict):
            return
        self.api.call(
            method="put",
            url=f"/2.2/eeros/{self.id}/nightlight/settings",
            json=json,
        )

    def set_nightlight_ambient(self) -> None:
        json = dict(enabled=True, schedule=dict(enabled=False))
        self._set_nightlight(json=json)

    def set_nightlight_brightness(self, value: int) -> None:
        if not isinstance(value, int):
            return
        json = dict(
            enabled=True,
            brightness_percentage=value,
            schedule=dict(
                enabled=True,
                on=self.nightlight_schedule[0],
                off=self.nightlight_schedule[1],
            ),
        )
        self._set_nightlight(json=json)

    def set_nightlight_disabled(self) -> None:
        json = dict(enabled=False)
        self._set_nightlight(json=json)

    def set_nightlight_schedule(self, time_on: str=None, time_off: str=None) -> None:
        if not isinstance(time_on, str) or not isinstance(time_off, str):
            return
        if time_on is None:
            time_on = self.nightlight_schedule[0]
        if time_off is None:
            time_off = self.nightlight_schedule[1]
        json = dict(enabled=True, schedule=dict(enabled=True, on=time_on, off=time_off))
        self._set_nightlight(json=json)

    @property
    def nightlight_schedule_on_hour(self) -> str:
        return self.nightlight_schedule[0].split(":")[0]

    @nightlight_schedule_on_hour.setter
    def nightlight_schedule_on_hour(self, value: int) -> None:
        if not isinstance(value, int):
            return
        self.set_nightlight_schedule(
            time_on=f"{self._format_time(value)}:{self.nightlight_schedule_on_minute}",
        )

    @property
    def nightlight_schedule_on_minute(self) -> str:
        return self.nightlight_schedule[0].split(":")[1]

    @nightlight_schedule_on_minute.setter
    def nightlight_schedule_on_minute(self, value: int) -> None:
        if not isinstance(value, int):
            return
        self.set_nightlight_schedule(
            time_on=f"{self.nightlight_schedule_on_hour}:{self._format_time(value)}",
        )

    @property
    def nightlight_schedule_off_hour(self) -> str:
        return self.nightlight_schedule[1].split(":")[0]

    @nightlight_schedule_off_hour.setter
    def nightlight_schedule_off_hour(self, value: int) -> None:
        if not isinstance(value, int):
            return
        self.set_nightlight_schedule(
            time_off=f"{self._format_time(value)}:{self.nightlight_schedule_off_minute}",
        )

    @property
    def nightlight_schedule_off_minute(self) -> str:
        return self.nightlight_schedule[1].split(":")[1]

    @nightlight_schedule_off_minute.setter
    def nightlight_schedule_off_minute(self, value: int) -> None:
        if not isinstance(value, int):
            return
        self.set_nightlight_schedule(
            time_off=f"{self.nightlight_schedule_off_hour}:{self._format_time(value)}",
        )

    def _format_time(self, value: int) -> str | None:
        if not isinstance(value, int):
            return
        if value < 10:
            return f"0{value}"
        return str(value)
