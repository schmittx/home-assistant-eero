"""Eero API"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

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
from .util import backup_access_point_ok

_LOGGER = logging.getLogger(__name__)


class EeroException(Exception):
    def __init__(
            self,
            code: int = None,
            error: str = None,
            server_time: str = None,
        ):
        super(EeroException, self).__init__()
        self.code = code
        self.error = error
        self.server_time = server_time
        message = "\n- EeroException"
        if self.code:
            message = f"{message}\n- Code: {self.code}"
        if self.error:
            message = f"{message}\n- Error: {self.error}"
        if self.server_time:
            message = f"{message}\n- Server time: {self.server_time}"
        _LOGGER.debug(message)


class EeroAPI(object):

    def __init__(
        self,
        activity: dict = {},
        save_location: str = None,
        show_eero_logo: bool = False,
        user_token: str = None,
    ) -> None:
        self.activity = activity
        self.data = EeroAccount(self, {})
        self.default_qr_code = open(EERO_LOGO_ICON, "rb").read() if show_eero_logo else None
        self.save_location = save_location
        self.session = requests.Session()
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
            response = self.refresh(lambda:
                self.session.delete(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == METHOD_GET:
            response = self.refresh(lambda:
                self.session.get(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == METHOD_POST:
            response = self.refresh(lambda:
                self.session.post(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == METHOD_PUT:
            response = self.refresh(lambda:
                self.session.put(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        response = self.parse_response(response=response)
        self.save_response(response=response, name=url)
        return response

    def define_period(self, period: str, timezone: str) -> tuple:
        start, end, cadence = None, None, None
        now = datetime.datetime.now(tz=pytz.timezone(timezone))
        if period == PERIOD_DAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta.relativedelta(days=1) - datetime.timedelta(minutes=1)
            cadence = CADENCE_HOURLY
        elif period == PERIOD_WEEK:
            start = now - relativedelta.relativedelta(days=now.weekday()+1)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta.relativedelta(weeks=1) - datetime.timedelta(minutes=1)
            cadence = CADENCE_DAILY
        elif period == PERIOD_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta.relativedelta(months=1) - datetime.timedelta(minutes=1)
            cadence = CADENCE_DAILY
        else:
            return (start, end, cadence)
        start = f"{start.astimezone(pytz.utc).replace(tzinfo=None).isoformat()}Z"
        end = f"{end.astimezone(pytz.utc).replace(tzinfo=None).isoformat()}Z"
        return (start, end, cadence)

    def get_release_notes(self, url: str) -> dict[str, Any] | None:
        if url:
            response = self.session.get(url=url)
            if response.status_code not in [200]:
                _LOGGER.warning(f"Unable to get release notes\n- Code: {response.status_code}\n- URL: {url}")
                return None
            text = json.loads(response.text)
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

    def parse_response(self, response: requests.Response) -> dict[str, Any]:
        text = json.loads(response.text)
        if response.status_code not in [200, 202]:
            _LOGGER.error(f"Parsing response was unsuccessful with status code: {response.status_code}")
            meta = text.get("meta")
            raise EeroException(
                code=meta.get("code"),
                error=meta.get("error"),
                server_time=meta.get("server_time"),
            )
        return text.get("data")

    def refresh(self, function: Callable) -> requests.Response:
        response = function()
        if response.status_code not in [200]:
            text = json.loads(response.text)
            error = text.get("meta", {}).get("error")
            if all(
                [
                    response.status_code == 401,
                    any(
                        [
                            error == "error.session.invalid",
                            error == "error.session.refresh",
                        ]
                    )
                ]
            ):
                _LOGGER.warning(f"Session has expired and is invalid\n- Code: {response.status_code}\n- Error: {error}")
                self.login_refresh()
                response = function()
        return response

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

    def update(self, conf_networks: list[int] | None = None) -> EeroAccount:
        try:
            account = self.call(method=METHOD_GET, url=URL_ACCOUNT)
            networks = []
            for network in account["networks"]["data"]:
                network_url = network["url"]
                if any(
                    [
                        conf_networks is None,
                        conf_networks and network_url.replace("/2.2/networks/", "") in conf_networks,
                    ]
                ):
                    network_data = self.call(method=METHOD_GET, url=network_url)
                    network_data["thread"] = self.call(
                        method=METHOD_GET,
                        url=network_data["resources"]["thread"],
                    )
                    if backup_access_point_ok(
                        capable=network_data["capabilities"]["backup_access_point"]["capable"],
                        requirements=network_data["capabilities"]["backup_access_point"]["requirements"],
                    ):
                        backup_access_points = self.call(
                            method=METHOD_GET,
                            url=f"{network['url']}/backup_access_points",
                        )
                        network_data["backup_access_points"] = {
                            "count": len(backup_access_points),
                            "data": backup_access_points,
                        }
                    for resource in ["profiles", "devices"]:
                        resource_data = self.call(
                            method=METHOD_GET,
                            url=network_data["resources"][resource],
                        )
                        network_data[resource] = {
                            "count": len(resource_data),
                            "data": resource_data,
                        }
                    update_data = network_data["updates"]
                    update_data["release_notes"] = self.get_release_notes(
                        url=update_data["manifest_resource"],
                    )
                    network_data["updates"] = update_data

                    network_id = network_data["url"].replace("/2.2/networks/", "")
                    activity_data = {}
                    for resource, activities in self.activity.get(network_id, {}).items():
                        resource = RESOURCE_MAP.get(resource, resource)
                        activity_data[resource] = {}
                        for activity in activities:
                            activity_data[resource][activity] = self.update_activity(
                                activity=activity,
                                network_url=network["url"],
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

    def update_activity(
            self,
            activity: str,
            network_url: str,
            resource: str,
            timezone: str,
        ) -> list[dict]:
        activity_url = ACTIVITY_MAP[activity][0].format(network_url)
        if resource != "network":
            activity_url = f"{activity_url}/{resource}"
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
