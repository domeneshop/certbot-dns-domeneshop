import json
import logging

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

API_BASE = "https://api.domeneshop.no/v0"

VALID_TYPES = [
    "A",
    "AAAA",
    "CNAME",
    "ANAME",
    "TLSA",
    "MX",
    "SRV",
    "DS",
    "CAA",
    "NS",
    "TXT",
]

COMMON_KEYS = {"host", "data", "ttl", "type"}

VALID_KEYS = {
    "MX": {"priority"},
    "SRV": {"priority", "weight", "port"},
    "TLSA": {"usage", "selector", "dtype"},
    "DS": {"tag", "alg", "digest"},
    "CAA": {"flags", "tag"},
}


class DomeneshopError(Exception):
    def __init__(self, status_code, error):
        self.status_code = status_code
        self.error_code = error.get("code")
        self.help = error.get("help")

        error_message = "{0} {1}. {2}".format(
            self.status_code, self.error_code, self.help
        )

        super().__init__(error_message)


class Client:
    def __init__(self, client_id, client_secret):
        self._token = HTTPBasicAuth(client_id, client_secret)

    def get_domains(self):
        resp = self._request("GET", "/domains")
        domains = resp.json()
        return domains

    def get_domain(self, domain_id):
        resp = self._request("GET", "/domains/{0}".format(domain_id))
        domains = resp.json()
        return domains

    def get_records(self, domain_id):
        resp = self._request("GET", "/domains/{0}/dns".format(domain_id))
        records = resp.json()
        return records

    def get_record(self, domain_id, record_id):
        resp = self._request("GET", "/domains/{0}/dns/{1}".format(domain_id, record_id))
        records = resp.json()
        return records

    def create_record(self, domain_id, record):
        """Create a new DNS record.

        Return the ID of the newly created record."""

        self._validate_record(record)
        resp = self._request("POST", "/domains/{0}/dns".format(domain_id), data=record)

        record_id = resp.headers.get("location").split("/")[-1]
        return int(record_id)

    def _validate_record(self, record):
        """Perform primitive prevalidation of DNS record. The rest is done by the API."""

        record_keys = set(record.keys())
        record_type = record.get("type")

        if record_type not in VALID_TYPES:
            raise TypeError(
                "Record has invalid type. Valid types: {0}".format(VALID_TYPES)
            )

        required_keys = COMMON_KEYS | VALID_KEYS.get(record_type, set())

        if record_keys != required_keys:
            raise TypeError(
                "Record is missing or has invalid keys. Required keys: {0}".format(
                    required_keys
                )
            )

    def modify_record(self, domain_id, record_id, record) -> None:
        self._validate_record(record)
        self._request(
            "PUT", "/domains/{0}/dns/{1}".format(domain_id, record_id), data=record
        )

    def delete_record(self, domain_id, record_id) -> None:
        self._request("DELETE", "/domains/{0}/dns/{1}".format(domain_id, record_id))

    def _request(self, method="GET", endpoint="/", data=None, params=None):
        if not data:
            data = {}
        if not params:
            params = {}

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        resp = requests.request(
            method,
            API_BASE + endpoint,
            data=json.dumps(data),
            params=params,
            headers=headers,
            auth=self._token,
        )
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                data = resp.json()
            except json.JSONDecodeError:
                data = {"error": resp.status_code, "help": "A server error occurred."}
            raise DomeneshopError(resp.status_code, data) from None
        else:
            return resp
