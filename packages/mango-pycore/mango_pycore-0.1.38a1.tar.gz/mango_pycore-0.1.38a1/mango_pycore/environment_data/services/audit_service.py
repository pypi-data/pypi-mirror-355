import json
import logging

import requests


class AuditServiceError(Exception):
    def __init__(self, message, url, api_key):
        self.message = message
        self.url = url
        self.api_key = api_key

    def __str__(self):
        return f"message: {self.message}  url: {self.url}  api-key: {self.api_key}"


class AuditService:
    def __init__(self, logger=logging):
        self._log = logger

    def create_audit_log(
            self,
            origin: str,
            url: str,
            api_key: str,
            data: dict
    ):
        url = f"{url}/audit"
        headers = {
            "Origin": origin,
            "X-Api-Key": api_key
        }
        response = requests.post(
            url=url,
            headers=headers,
            json=data
        )

        if response.status_code == 400:
            self._log.error(f"Bad Request: message: {json.dumps(response.json())}  url: {url}  api-key: {api_key}")

            raise AuditServiceError(
                message=json.dumps(response.json()),
                url=url,
                api_key=api_key,
            )

        if response.status_code == 403:
            self._log.error(f"Access Denied: message: {json.dumps(response.json())}  url: {url}  api-key: {api_key}")

            raise AuditServiceError(
                message=json.dumps(response.json()),
                url=url,
                api_key=api_key,
            )

        if response.status_code == 500:
            self._log.error(
                f"Internal Server Error: message: {json.dumps(response.json())}  url: {url}  api-key: {api_key}"
            )

            raise AuditServiceError(
                message=json.dumps(response.json()),
                url=url,
                api_key=api_key,
            )


def get_audit_service(logger=logging):
    return AuditService(
        logger=logger
    )
