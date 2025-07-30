import json
import logging
import re
from typing import Union

import httpx

from mousetools.auth import auth_obj

logger = logging.getLogger(__name__)


class CouchbaseMixin:
    _couchbase_url = "https://" + auth_obj._environments["syncGatewayUrl"].split("//")[1].rstrip("/")
    _headers: dict = auth_obj.get_couchbase_headers()

    def get_channel_data(self, channel_name: str) -> Union[dict, None]:
        """
        Sends a request to the Disney Couchbase API with the given channel ID and returns the data.

        Args:
            channel_name (str): Couchbase channel to request data from.

        Returns:
            (dict): The disney data.
        """

        payload = {
            "docs": [
                {"id": channel_name},
            ],
            "json": True,
        }

        logger.info("Sending request for channel data: %s", channel_name)
        response = httpx.post(self._couchbase_url + "/_bulk_get", json=payload, headers=self._headers)
        logger.debug("Response status for %s: %s", channel_name, response.status_code)
        data = None
        try:
            response.raise_for_status()
            raw_data = response.text

            cont_reg = re.compile(r"\w+-\w+:\s\w+\/\w+")
            raw_data = re.sub(cont_reg, "", raw_data)
            raw_data = raw_data.splitlines()

            for line in raw_data:
                if line != "" and line[0] != "-":
                    try:
                        data = json.loads(line)
                    except Exception:
                        logger.debug("Failed to parse line: %s", line)
                        continue
        except httpx.HTTPError as err:
            logger.error("Request failed: %s", err)
            return None

        return data

    def get_channel_changes(self, channel_name: str, since: Union[int, None] = None) -> Union[dict, None]:
        """Sends a request to the Disney Couchbase API with the given channel ID and returns the data.

        Args:
            channel_name (str): Couchbase channel to request data from.
            since (Union[int, None], optional): Since when to get changes. Defaults to None.

        Returns:
            Union[dict, None]: The disney data.
        """
        try:
            payload = {
                "channels": channel_name,
                "style": "all_docs",
                "filter": "sync_gateway/bychannel",
                "feed": "normal",
                "heartbeat": 30000,
            }
            if since:
                payload["since"] = since

            logger.info("Sending request for channel changes: %s", channel_name)
            response = httpx.post(self._couchbase_url + "/_changes", json=payload, headers=self._headers)
            logger.debug("Response status for %s: %s", channel_name, response.status_code)
            data = response.raise_for_status().json()
        except httpx.HTTPError as err:
            logger.error("Request failed: %s", err)
            return None

        return data
