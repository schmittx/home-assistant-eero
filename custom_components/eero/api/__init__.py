"""Eero API."""

from __future__ import annotations

from collections.abc import Callable
import datetime
import json
import logging
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import aiofiles
from dateutil import relativedelta
import requests

from .account import EeroAccount
from .const import (
    ACTIVITY_MAP,
    API_ENDPOINT,
    CADENCE_DAILY,
    CADENCE_HOURLY,
    EERO_LOGO_ICON,
    METHOD_DELETE,
    METHOD_GET,
    METHOD_POST,
    METHOD_PUT,
    PERIOD_DAY,
    PERIOD_MONTH,
    PERIOD_WEEK,
    RESOURCE_MAP,
    URL_ACCOUNT,
)
from .util import backup_access_point_ok, premium_ok

_LOGGER = logging.getLogger(__name__)


class EeroException(Exception):
    """EeroException."""

    def __init__(
        self,
        code: int | None = None,
        error: str | None = None,
        message: str | None = None,
        payload: str | None = None,
        server_time: str | None = None,
    ) -> None:
        """Initialize."""
        super().__init__()
        self.code = code
        self.error = error
        self.message = message
        self.payload = payload
        self.server_time = server_time
        exception = self.__class__.__name__
        if self.code:
            exception = f"{exception}\n- Code: {self.code}"
        if self.error:
            exception = f"{exception}\n- Error: {self.error}"
        if self.message:
            exception = f"{exception}\n- Message: {self.message}"
        if self.payload:
            exception = f"{exception}\n- Payload: {self.payload}"
        if self.server_time:
            exception = f"{exception}\n- Server time: {self.server_time}"
        _LOGGER.warning(exception)


class EeroAPI:
    """EeroAPI."""

    def __init__(
        self,
        save_location: str | None = None,
        show_eero_logo: dict[str, bool] | None = None,
        user_token: str | None = None,
    ) -> None:
        """Initialize."""
        self.data = EeroAccount(self, {})
        self.default_qr_code: bytes | None = None
        self.save_location = save_location
        self.session = requests.Session()
        self.show_eero_logo = show_eero_logo
        self.user_token = user_token
        if self.show_eero_logo is None:
            self.show_eero_logo = {}

    @property
    def cookie(self) -> dict:
        """Cookie."""
        if self.user_token:
            return {"s": self.user_token}
        return {}

    def call(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Call."""
        if method not in [METHOD_DELETE, METHOD_GET, METHOD_POST, METHOD_PUT]:
            return None
        _LOGGER.debug("Calling API with method: %s and URL: %s", method, url)
        if method == METHOD_DELETE:
            response = self.parse_response(
                lambda: self.session.delete(
                    url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs
                )
            )
        elif method == METHOD_GET:
            response = self.parse_response(
                lambda: self.session.get(
                    url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs
                )
            )
        elif method == METHOD_POST:
            response = self.parse_response(
                lambda: self.session.post(
                    url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs
                )
            )
        elif method == METHOD_PUT:
            response = self.parse_response(
                lambda: self.session.put(
                    url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs
                )
            )
        self.save_response(response=response, name=url)
        return response

    def define_period(self, period: str, timezone: str) -> tuple:
        """Define period."""
        start, end, cadence = None, None, None
        now = datetime.datetime.now(tz=ZoneInfo(timezone))
        if period == PERIOD_DAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = (
                start
                + relativedelta.relativedelta(days=1)
                - datetime.timedelta(seconds=1)
            )
            cadence = CADENCE_HOURLY
        elif period == PERIOD_WEEK:
            start = now - relativedelta.relativedelta(days=now.weekday() + 1)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = (
                start
                + relativedelta.relativedelta(weeks=1)
                - datetime.timedelta(seconds=1)
            )
            cadence = CADENCE_DAILY
        elif period == PERIOD_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = (
                start
                + relativedelta.relativedelta(months=1)
                - datetime.timedelta(seconds=1)
            )
            cadence = CADENCE_DAILY
        else:
            return (start, end, cadence)
        start = f"{start.astimezone(datetime.UTC).replace(tzinfo=None).isoformat()}Z"
        end = f"{end.astimezone(datetime.UTC).replace(tzinfo=None).isoformat()}Z"
        return (start, end, cadence)

    async def generate_default_qr_code(self) -> None:
        """Generate default QR code."""
        async with aiofiles.open(EERO_LOGO_ICON, "rb") as file:
            self.default_qr_code = await file.read()

    def get_release_notes(self, url: str) -> dict[str, Any] | None:
        """Get release notes."""
        if url:
            response = self.timeout(lambda: self.session.get(url=url))
            if not response.ok:
                raise EeroException(
                    code=response.status_code,
                    error=response.reason,
                    message=f"Unable to get release notes from URL: {url}",
                    payload=response.text,
                )
            text = self.decode_json(response)
            self.save_response(response=text, name="release_notes")
            return text
        return None

    def login(self, login: str | int) -> dict[str, Any]:
        """Login."""
        _LOGGER.debug("Using login: %s", login)
        response = self.call(
            method=METHOD_POST,
            url="/2.2/login",
            json={"login": login},
        )
        self.user_token = response["user_token"]
        return response

    def login_refresh(self) -> dict[str, Any]:
        """Login refresh."""
        _LOGGER.debug("Refreshing session")
        response = self.call(
            method=METHOD_POST,
            url="/2.2/login/refresh",
        )
        self.user_token = response["user_token"]
        return response

    def login_verify(self, code: str) -> dict[str, Any]:
        """Login verify."""
        _LOGGER.debug("Verifying login with code: %s", code)
        return self.call(
            method=METHOD_POST,
            url="/2.2/login/verify",
            json={"code": code},
        )

    def decode_json(self, response: requests.Response) -> dict[str, Any]:
        """Decode JSON."""
        try:
            return json.loads(response.text)
        except json.decoder.JSONDecodeError as exception:
            raise EeroException(
                code=response.status_code,
                error=response.reason,
                message="Unable to decode JSON",
                payload=response.text,
            ) from exception

    def parse_response(self, function: Callable) -> dict[str, Any]:
        """Parse response."""
        response = self.timeout(function)
        if not response.ok:
            text = self.decode_json(response)
            meta = text.get("meta", {})
            code, error = meta.get("code"), meta.get("error")
            if all(
                [
                    code == 401,
                    any(
                        [
                            error == "error.session.invalid",
                            error == "error.session.refresh",
                        ]
                    ),
                ]
            ):
                _LOGGER.debug("Session has expired and is invalid")
                self.login_refresh()
                response = self.timeout(function)
            else:
                raise EeroException(
                    code=response.status_code,
                    error=response.reason,
                    message=f"Bad response received from URL: {response.url}",
                    payload=response.text,
                )
        text = self.decode_json(response)
        return text.get("data")

    def timeout(self, function: Callable) -> requests.Response:
        """Timeout."""
        try:
            return function()
        except requests.exceptions.Timeout as exception:
            raise EeroException(
                message="Request timed out",
            ) from exception

    def save_response(self, response: dict[str, Any] | None, name="response") -> None:
        """Save response."""
        if self.save_location and response:
            if not Path(self.save_location).is_dir():
                _LOGGER.debug("Creating directory: %s", self.save_location)
                Path(self.save_location).mkdir()
            name = name.replace("/", "_").replace(".", "_")
            file_path_name = f"{self.save_location}/{name}.json"
            _LOGGER.debug("Saving response: %s", file_path_name)
            with Path(file_path_name).open(mode="w", encoding="utf-8") as file:
                json.dump(
                    obj=response,
                    fp=file,
                    indent=4,
                    default=lambda o: "not-serializable",
                    sort_keys=True,
                )
            file.close()

    def update(
        self,
        config: dict[str, EeroUpdateConfig] | None = None,
    ) -> EeroAccount:
        """Update."""
        if config is None:
            config = {}
        try:
            account = self.call(method=METHOD_GET, url=URL_ACCOUNT)
            networks = []
            for network in account["networks"]["data"]:
                network_url = network["url"]
                network_id = network_url.replace("/2.2/networks/", "")
                if any(
                    [
                        not config,
                        network_id in config,
                    ]
                ):
                    network_data = self.call(method=METHOD_GET, url=network_url)
                    network_data["thread"] = self.call(
                        method=METHOD_GET,
                        url=network_data["resources"]["thread"],
                    )

                    if all(
                        [
                            any(
                                [
                                    not config,
                                    config.get(
                                        network_id, EeroUpdateConfig()
                                    ).get_backup_access_points,
                                ]
                            ),
                            backup_access_point_ok(
                                capable=network_data["capabilities"][
                                    "backup_access_point"
                                ]["capable"],
                                requirements=network_data["capabilities"][
                                    "backup_access_point"
                                ]["requirements"],
                            ),
                            premium_ok(
                                capable=network_data["capabilities"]["premium"][
                                    "capable"
                                ],
                                status=network_data["premium_status"],
                            ),
                        ]
                    ):
                        backup_access_points = self.call(
                            method=METHOD_GET,
                            url=f"{network_url}/backup_access_points",
                        )
                        network_data["backup_access_points"] = {
                            "count": len(backup_access_points),
                            "data": backup_access_points,
                        }

                    if any(
                        [
                            not config,
                            config.get(network_id, EeroUpdateConfig()).get_devices,
                        ]
                    ):
                        network_data["devices"] = self.get_resource_data(
                            network_data, "devices"
                        )

                    if any(
                        [
                            not config,
                            config.get(network_id, EeroUpdateConfig()).get_profiles,
                        ]
                    ):
                        network_data["profiles"] = self.get_resource_data(
                            network_data, "profiles"
                        )

                    update_data = network_data["updates"]
                    if config.get(network_id, EeroUpdateConfig()).get_release_notes:
                        update_data["release_notes"] = self.get_release_notes(
                            url=update_data["manifest_resource"],
                        )
                    network_data["updates"] = update_data

                    network_id = network_url.replace("/2.2/networks/", "")
                    activity_data = {}
                    for resource, activities in config.get(
                        network_id, EeroUpdateConfig()
                    ).activity.items():
                        resource = RESOURCE_MAP.get(resource, resource)
                        activity_data[resource] = {}
                        for activity in activities:
                            if resource == "profiles":
                                activity_data[resource][activity] = {}
                                for profile_id in config.get(
                                    network_id, EeroUpdateConfig()
                                ).profiles:
                                    activity_data[resource][activity][profile_id] = (
                                        self.update_activity(
                                            activity=activity,
                                            network_url=network_url,
                                            profile_id=profile_id,
                                            resource=resource,
                                            timezone=network_data["timezone"]["value"],
                                        )
                                    )
                            else:
                                activity_data[resource][activity] = (
                                    self.update_activity(
                                        activity=activity,
                                        network_url=network_url,
                                        profile_id=None,
                                        resource=resource,
                                        timezone=network_data["timezone"]["value"],
                                    )
                                )
                    network_data["activity"] = activity_data
                    networks.append(network_data)
            account["networks"]["data"] = networks
            self.save_response(response=account, name="update_data")
            self.data = EeroAccount(self, account)
        except EeroException:
            return self.data
        return self.data

    def get_resource_data(
        self,
        network_data: dict,
        resource: str,
    ) -> dict:
        """Get resource data."""
        resource_data = self.call(
            method=METHOD_GET,
            url=network_data["resources"][resource],
        )
        return {
            "count": len(resource_data),
            "data": resource_data,
        }

    def update_activity(
        self,
        activity: str,
        network_url: str,
        profile_id: int,
        resource: str,
        timezone: str,
    ) -> list[dict]:
        """Update activity."""
        activity_url = ACTIVITY_MAP[activity][0].format(network_url)
        if resource != "network":
            activity_url = f"{activity_url}/{resource}"
        if resource == "profiles":
            activity_url = f"{activity_url}/{profile_id}"
        start, end, cadence = self.define_period(
            period=ACTIVITY_MAP[activity][2],
            timezone=timezone,
        )
        json_data = {
            "start": start,
            "end": end,
            "cadence": cadence,
            "timezone": timezone,
        }
        if ACTIVITY_MAP[activity][1]:
            json_data["insight_type"] = ACTIVITY_MAP[activity][1]
        data = self.call(
            method=METHOD_GET,
            url=activity_url,
            json=json_data,
        )
        return data.get("insights", data.get("series", data.get("values")))


class EeroUpdateConfig:
    """A class that describes an Eero update config."""

    def __init__(
        self,
        activity: dict | None = None,
        profiles: list | None = None,
        get_backup_access_points: bool = False,
        get_devices: bool = False,
        get_release_notes: bool = False,
    ) -> None:
        """Initialize."""
        self.activity = activity
        self.profiles = profiles
        self.get_backup_access_points = get_backup_access_points
        self.get_devices = get_devices
        self.get_profiles = bool(profiles)
        self.get_release_notes = get_release_notes
        if self.activity is None:
            self.activity = {}
        if self.profiles is None:
            self.profiles = []
