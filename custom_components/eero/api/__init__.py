"""Eero API"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import aiofiles
import datetime
from dateutil import relativedelta
import json
import logging
import os
import pytz
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

    def __init__(
            self,
            code: int = None,
            error: str = None,
            message: str = None,
            payload: str = None,
            server_time: str = None,
        ) -> None:
        super(EeroException, self).__init__()
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


class EeroAPI(object):

    def __init__(
        self,
        save_location: str = None,
        show_eero_logo: dict[str, bool] = {},
        user_token: str = None,
    ) -> None:
        self.data = EeroAccount(self, {})
        self.default_qr_code: bytes | None = None
        self.save_location = save_location
        self.session = requests.Session()
        self.show_eero_logo = show_eero_logo
        self.user_token = user_token

    @property
    def cookie(self) -> dict:
        if self.user_token:
            return {"s": self.user_token}
        return {}

    def call(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        if method not in [METHOD_DELETE, METHOD_GET, METHOD_POST, METHOD_PUT]:
            return
        _LOGGER.debug(f"Calling API with method: {method} and URL: {url}")
        if method == METHOD_DELETE:
            response = self.parse_response(lambda:
                self.session.delete(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == METHOD_GET:
            response = self.parse_response(lambda:
                self.session.get(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == METHOD_POST:
            response = self.parse_response(lambda:
                self.session.post(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == METHOD_PUT:
            response = self.parse_response(lambda:
                self.session.put(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        self.save_response(response=response, name=url)
        return response

    def define_period(self, period: str, timezone: str) -> tuple:
        start, end, cadence = None, None, None
        now = datetime.datetime.now(tz=pytz.timezone(timezone))
        if period == PERIOD_DAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta.relativedelta(days=1) - datetime.timedelta(seconds=1)
            cadence = CADENCE_HOURLY
        elif period == PERIOD_WEEK:
            start = now - relativedelta.relativedelta(days=now.weekday()+1)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta.relativedelta(weeks=1) - datetime.timedelta(seconds=1)
            cadence = CADENCE_DAILY
        elif period == PERIOD_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta.relativedelta(months=1) - datetime.timedelta(seconds=1)
            cadence = CADENCE_DAILY
        else:
            return (start, end, cadence)
        start = f"{start.astimezone(pytz.utc).replace(tzinfo=None).isoformat()}Z"
        end = f"{end.astimezone(pytz.utc).replace(tzinfo=None).isoformat()}Z"
        return (start, end, cadence)

    async def generate_default_qr_code(self) -> None:
        async with aiofiles.open(EERO_LOGO_ICON, "rb") as file:
            self.default_qr_code = await file.read()

    def get_release_notes(self, url: str) -> dict[str, Any] | None:
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
        _LOGGER.debug(f"Using login: {login}")
        response = self.call(
            method=METHOD_POST,
            url="/2.2/login",
            json={"login": login},
        )
        self.user_token = response["user_token"]
        return response

    def login_refresh(self) -> dict[str, Any]:
        _LOGGER.debug(f"Refreshing session")
        response = self.call(
            method=METHOD_POST,
            url="/2.2/login/refresh",
        )
        self.user_token = response["user_token"]
        return response

    def login_verify(self, code: str) -> dict[str, Any]:
        _LOGGER.debug(f"Verifying login with code: {code}")
        response = self.call(
            method=METHOD_POST,
            url="/2.2/login/verify",
            json={"code": code},
        )
        return response

    def decode_json(self, response: requests.Response) -> dict[str, Any]:
        try:
            return json.loads(response.text)
        except json.decoder.JSONDecodeError:
            raise EeroException(
                code=response.status_code,
                error=response.reason,
                message="Unable to decode JSON",
                payload=response.text,
            )     

    def parse_response(self, function: Callable) -> dict[str, Any]:
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
        try:
            return function()
        except requests.exceptions.Timeout:
            raise EeroException(
                message="Request timed out",
            )

    def save_response(self, response: dict[str, Any] | None, name="response") -> None:
        if self.save_location and response:
            if not os.path.isdir(self.save_location):
                os.mkdir(self.save_location)
            name = name.replace("/", "_").replace(".", "_")
            file_path_name = f"{self.save_location}/{name}.json"
            _LOGGER.debug(f"Saving response: {file_path_name}")
            with open(file_path_name, "w") as file:
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
            config: dict[str, EeroUpdateConfig] = {},
    ) -> EeroAccount:
        try:
            account = self.call(method=METHOD_GET, url=URL_ACCOUNT)
            networks = []
            for network in account["networks"]["data"]:
                network_url = network["url"]
                network_id = network_url.replace("/2.2/networks/", "")
                if any(
                    [
                        not config,
                        network_id in config.keys(),
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
                                    config.get(network_id, EeroUpdateConfig()).get_backup_access_points,
                                ]
                            ),
                            backup_access_point_ok(
                                capable=network_data["capabilities"]["backup_access_point"]["capable"],
                                requirements=network_data["capabilities"]["backup_access_point"]["requirements"],
                            ),
                            premium_ok(
                                capable=network_data["capabilities"]["premium"]["capable"],
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
                        network_data["devices"] = self.get_resource_data(network_data, "devices")

                    if any(
                        [
                            not config,
                            config.get(network_id, EeroUpdateConfig()).get_profiles,
                        ]
                    ):
                        network_data["profiles"] = self.get_resource_data(network_data, "profiles")

                    update_data = network_data["updates"]
                    if config.get(network_id, EeroUpdateConfig()).get_release_notes:
                        update_data["release_notes"] = self.get_release_notes(
                            url=update_data["manifest_resource"],
                        )
                    network_data["updates"] = update_data

                    network_id = network_url.replace("/2.2/networks/", "")
                    activity_data = {}
                    for resource, activities in config.get(network_id, EeroUpdateConfig()).activity.items():
                        resource = RESOURCE_MAP.get(resource, resource)
                        activity_data[resource] = {}
                        for activity in activities:
                            if resource == "profiles":
                                activity_data[resource][activity] = {}
                                for profile_id in config.get(network_id, EeroUpdateConfig()).profiles:
                                    activity_data[resource][activity][profile_id] = self.update_activity(
                                        activity=activity,
                                        network_url=network_url,
                                        profile_id=profile_id,
                                        resource=resource,
                                        timezone=network_data["timezone"]["value"],
                                    )
                            else:
                                activity_data[resource][activity] = self.update_activity(
                                    activity=activity,
                                    network_url=network_url,
                                    profile_id=None,
                                    resource=resource,
                                    timezone=network_data["timezone"]["value"],
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
        activity_url = ACTIVITY_MAP[activity][0].format(network_url)
        if resource != "network":
            activity_url = f"{activity_url}/{resource}"
        if resource == "profiles":
            activity_url = f"{activity_url}/{profile_id}"
        start, end, cadence = self.define_period(
            period=ACTIVITY_MAP[activity][2],
            timezone=timezone,
        )
        json = {
            "start": start,
            "end": end,
            "cadence": cadence,
            "timezone": timezone,
        }
        if ACTIVITY_MAP[activity][1]:
            json["insight_type"] = ACTIVITY_MAP[activity][1]
        data = self.call(
            method=METHOD_GET,
            url=activity_url,
            json=json,
        )
        return data.get("insights", data.get("series", data.get("values")))


class EeroUpdateConfig:
    """A class that describes an Eero update config."""

    def __init__(
        self,
        activity: dict = {},
        profiles: list = [],
        get_backup_access_points: bool = False,
        get_devices: bool = False,
        get_release_notes: bool = False,
    ) -> None:
        self.activity = activity
        self.profiles = profiles
        self.get_backup_access_points = get_backup_access_points
        self.get_devices = get_devices
        self.get_profiles = bool(profiles)
        self.get_release_notes = get_release_notes