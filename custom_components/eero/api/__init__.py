"""Eero API"""
import datetime
from dateutil import relativedelta
import json
import os
import pytz
import requests

from .account import Account
from .const import (
    ACTIVITY_MAP,
    API_ENDPOINT,
    CADENCE_DAILY,
    CADENCE_HOURLY,
    MODEL_BEACON,
    PERIOD_DAY,
    PERIOD_MONTH,
    PERIOD_WEEK,
    RESOURCE_MAP,
    URL_ACCOUNT,
)


class EeroException(Exception):
    def __init__(self, status, error_message):
        super(EeroException, self).__init__()
        self.status = status
        self.error_message = error_message


class EeroAPI(object):

    def __init__(self, activity={}, save_location=None, user_token=None):
        self.activity = activity
        self.data = Account(self, {})
        self.save_location = save_location
        self.session = requests.Session()
        self.user_token = user_token

    @property
    def cookie(self):
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
        if data["meta"]["code"] not in [200, 201]:
            raise EeroException(data["meta"]["code"], data["meta"].get("error", ""))
        return data.get("data", "")

    def refresh(self, function):
        try:
            return function()
        except EeroException as exception:
            if (exception.status == 401 and exception.error_message == "error.session.refresh"):
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

    def update(self):
        try:
            account = self.call(method="get", url=URL_ACCOUNT)

            networks = list()
            for network in account["networks"]["data"]:
                network_data = self.call(method="get", url=network["url"])
                for index, eero in enumerate(network_data["eeros"]["data"]):
                    if eero["model"] == MODEL_BEACON:
                        eero_data = self.call(method="get", url=eero["url"])
                        network_data["eeros"]["data"][index] = eero_data
                for resource in ["profiles", "devices"]:
                    resource_data = self.call(method="get", url=network_data["resources"][resource])
                    network_data[resource] = dict(count=len(resource_data), data=resource_data)

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
            self.data = Account(self, account)
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
