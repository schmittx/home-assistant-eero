"""Eero API"""
from __future__ import annotations

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
    PERIOD_DAY,
    PERIOD_MONTH,
    PERIOD_WEEK,
    RESOURCE_MAP,
    STATE_ACTIVE,
    URL_ACCOUNT,
)

_LOGGER = logging.getLogger(__name__)


class EeroException(Exception):
    def __init__(self, response):
        super(EeroException, self).__init__()
        self.status_code = response.status_code
        data = json.loads(response.text)
        _LOGGER.error(f"Exception raised, status code: {self.status_code}, text: {data}")
        error = data.get("error", data.get("meta", {}))
        self.error_message = error.get("message", error.get("error"))


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
    def cookie(self) -> dict[str | None, str | None]:
        if self.user_token:
            return dict(s=self.user_token)
        return dict()

    def call(self, method, url, **kwargs):
        if method not in ["get", "post", "put"]:
            return
        if method == "get":
            response = self.refresh(lambda:
                self.session.get(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == "post":
            response = self.refresh(lambda:
                self.session.post(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        elif method == "put":
            response = self.refresh(lambda:
                self.session.put(url=f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
            )
        response = self.parse_response(response)
        self.save_response(response=response, name=url)
        return response

    def get_release_notes(self, url):
        if url:
            response = self.session.get(url=url)
            if response.status_code not in [200, 201]:
                raise EeroException(response)
            data = json.loads(response.text)
            self.save_response(response=data, name="release_notes")
            return data
        return None

    def define_period(self, period, timezone):
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

    def login(self, login):
        response = self.call(
            method="post",
            url="/2.2/login",
            json=dict(login=login),
        )
        self.user_token = response["user_token"]
        return response

    def login_refresh(self):
        response = self.call(
            method="post",
            url="/2.2/login/refresh",
        )
        self.user_token = response["user_token"]
        return response

    def login_verify(self, code):
        response = self.call(
            method="post",
            url="/2.2/login/verify",
            json=dict(code=code),
        )
        return response

    def parse_response(self, response):
        data = json.loads(response.text)
        if response.status_code in [200, 201]:
            return data.get("data", {})
        elif response.status_code == 202:
            return data
        raise EeroException(response)

    def refresh(self, function):
        try:
            return function()
        except EeroException as exception:
            if all(
                [
                    exception.status_code == 401,
                    any(
                        [
                            exception.error_message == "error.session.refresh",
                            exception.error_message == "error.session.invalid",
                        ]
                    )
                ]
            ):
                self.login_refresh()
                return function()
            else:
                raise

    def save_response(self, response, name="response"):
        if self.save_location and response:
            if not os.path.isdir(self.save_location):
                os.mkdir(self.save_location)
            name = name.replace("/", "_").replace(".", "_")
            with open(f"{self.save_location}/{name}.json", "w") as file:
                json.dump(response, file, default=lambda o: "not-serializable", indent=4, sort_keys=True)
            file.close()

    def update(self, conf_networks: list | None = None) -> dict:
        try:
            account = self.call(method="get", url=URL_ACCOUNT)

            networks = []
            for network in account["networks"]["data"]:
                network_url = network["url"]
                if any(
                    [
                        conf_networks is None,
                        conf_networks and network_url.replace("/2.2/networks/", "") in conf_networks,
                    ]
                ):
                    network_data = self.call(method="get", url=network_url)
                    network_data["thread"] = self.call(method="get", url=network_data["resources"]["thread"])
                    if network_data["premium_status"] == STATE_ACTIVE:
                        backup_access_points = self.call(method="get", url=f"{network['url']}/backup_access_points")
                        network_data["backup_access_points"] = dict(count=len(backup_access_points), data=backup_access_points)
                    for resource in ["profiles", "devices"]:
                        resource_data = self.call(method="get", url=network_data["resources"][resource])
                        network_data[resource] = dict(count=len(resource_data), data=resource_data)
                    update_data = network_data["updates"]
                    update_data["release_notes"] = self.get_release_notes(url=update_data["manifest_resource"])
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

    def update_activity(self, activity, network_url, resource, timezone):
        activity_url = ACTIVITY_MAP[activity][0].format(network_url)
        if resource != "network":
            activity_url = f"{activity_url}/{resource}"
        start, end, cadence = self.define_period(period=ACTIVITY_MAP[activity][2], timezone=timezone)
        json = dict(start=start, end=end, cadence=cadence, timezone=timezone)
        if ACTIVITY_MAP[activity][1]:
            json["insight_type"] = ACTIVITY_MAP[activity][1]
        data = self.call(
            method="get",
            url=activity_url,
            json=json,
        )
        return data.get("insights", data.get("series", data.get("values")))
