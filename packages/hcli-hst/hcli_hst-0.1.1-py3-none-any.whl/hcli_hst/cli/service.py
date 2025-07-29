import io
import sys
import os
import re
import time
import inspect
import logger
import requests
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime
from hcli_problem_details import *

logging = logger.Logger()

class Service:
    def __init__(self):
        self.base_url = "https://api.spacetraders.io/v2"
        self.token = os.getenv('SPACETRADERS_AGENT_TOKEN')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Authorization': f"Bearer {self.token}"
        }

    def _clean(self, param):
        if param is not None:
            return param.replace('"', '')
        return None

    def _get(self, endpoint, resource_id=None):
        url = f"{self.base_url}/{endpoint}"
        if resource_id is not None:
            url = f"{url}/{resource_id}"

        response = requests.get(url, headers=self.headers)


        if response.status_code >= 400:
            detail = "Error."
            try:
                if response.content:
                    detail = response.json()
            except ValueError as e:
                detail = response.text

            problem = ProblemDetail.from_status_code(
                status_code=response.status_code,
                instance=url,
                detail=detail
            )

            logging.error(problem.to_dict())
            raise problem

        return response.content

    def _post(self, endpoint, resource_id=None):
        url = f"{self.base_url}/{endpoint}"
        if resource_id is not None:
            url = f"{url}/{resource_id}"

        response = requests.post(url, headers=self.headers)

        if response.status_code >= 400:
            detail = "Error."
            try:
                if response.content:
                    detail = response.json()
            except ValueError as e:
                detail = response.text

            problem = ProblemDetail.from_status_code(
                status_code=response.status_code,
                instance=url,
                detail=detail
            )

            logging.error(problem.to_dict())
            raise problem

        return response.content

    def agent(self, agent_id=None):
        endpoint = "my/agent" if agent_id is None else "agents"
        return self._get(endpoint, self._clean(agent_id))

    def agents(self):
        return self._get("agents")

    def ships(self, ship_id=None):
        endpoint = "my/ships"
        return self._get(endpoint, self._clean(ship_id))

    def systems(self, system_id=None):
        return self._get("systems", self._clean(system_id))

    def server(self):
        return self._get("")

    def contracts(self, contract_id=None):
        return self._get("my/contracts", self._clean(contract_id))

    def contracts_accept(self, contract_id):
        contract_id = self._clean(contract_id)
        endpoint = f"my/contracts/{contract_id}/accept"
        return self._post(endpoint)


