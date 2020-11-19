"""Eero API"""
import json
import os
import re
import requests

from .account import Account
from .const import API_ENDPOINT, MODEL_BEACON, URL_ACCOUNT


class EeroException(Exception):
    def __init__(self, status, error_message):
        super(EeroException, self).__init__()
        self.status = status
        self.error_message = error_message


class EeroAPI(object):

    def __init__(self, user_token=None, save_location=None):
        self.data = None
        self.session = requests.Session()
        self.user_token = user_token
        self.save_location = save_location

    @property
    def cookie(self):
        if self.user_token:
            return dict(s=self.user_token)
        return dict()

    def id_from_url(self, id_or_url):
        match = re.search("^[0-9]+$", id_or_url)
        if match:
            return match.group(0)
        match = re.search(r"\/([0-9]+)$", id_or_url)
        if match:
            return match.group(1)

    def parse_response(self, response):
        data = json.loads(response.text)
        if data["meta"]["code"] not in [200, 201]:
            raise EeroException(data["meta"]["code"], data["meta"].get("error", ""))
        return data.get("data", "")

    def save_response(self, response, name="response"):
        if self.save_location and response:
            if not os.path.isdir(self.save_location):
                os.mkdir(self.save_location)
            name = name.replace("/", "_").replace(".", "_")
            with open(f"{self.save_location}/{name}.json", "w") as file:
                json.dump(response, file, indent=4)
            file.close()

    def get(self, url, **kwargs):
        response = self.refresh(lambda:
            self.session.get(f"{API_ENDPOINT}{url}", cookies=self.cookie, **kwargs)
        )
        response = self.parse_response(response)
        self.save_response(response=response, name=url)
        return response

    def post(self, url, data=None, json=None, **kwargs):
        response = self.refresh(lambda:
            self.session.post(f"{API_ENDPOINT}{url}", cookies=self.cookie, data=data, json=json, **kwargs)
        )
        response = self.parse_response(response)
        self.save_response(response=response, name=url)
        return response

    def put(self, url, data=None, **kwargs):
        response = self.refresh(lambda:
            self.session.put(f"{API_ENDPOINT}{url}", cookies=self.cookie, data=data, **kwargs)
        )
        response = self.parse_response(response)
        self.save_response(response=response, name=url)
        return response

    def login(self, login):
        response = self.post(
            url="/2.2/login",
            json=dict(login=login),
        )
        self.user_token = response["user_token"]
        return response

    def login_refresh(self):
        response = self.post(
            url="/2.2/login/refresh",
        )
        self.user_token = response["user_token"]
        return response

    def login_verify(self, code):
        response = self.post(
            url="/2.2/login/verify",
            json=dict(code=code),
        )
        return response

    def refresh(self, function):
        try:
            return function()
        except EeroException as exception:
            if (exception.status == 401 and exception.error_message == "error.session.refresh"):
                self.login_refresh()
                return function()
            else:
                raise

    def update(self):
        try:
            account = self.get(url=URL_ACCOUNT)

            networks = list()
            for network in account["networks"]["data"]:
                network_data = self.get(url=network["url"])
                for index, eero in enumerate(network_data["eeros"]["data"]):
                    if eero["model"] == MODEL_BEACON:
                        eero_data = self.get(url=eero["url"])
                        network_data["eeros"]["data"][index] = eero_data
                for resource in ["profiles", "devices"]:
                    resource_data = self.get(url=network_data["resources"][resource])
                    network_data[resource] = dict(count=len(resource_data), data=resource_data)
                networks.append(network_data)
            account["networks"]["data"] = networks
            self.data = Account(self, account)
        except EeroException as exception:
            return self.data
        return self.data
