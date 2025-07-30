import json
import logging
from typing import Union

import httpx

from mousetools.auth import auth_obj

logger = logging.getLogger(__name__)


class DisneyAPIMixin:
    def get_disney_data(self, url: str) -> Union[dict, None]:
        """
        Sends a request to the Disney API at the given url and returns the data.

        Args:
            url (str): API url to request data from.

        Returns:
            (Union[dict, None]): The disney data.
        """
        logger.info("Sending request to %s", url)
        response = httpx.get(url, headers=auth_obj.get_headers())
        logger.debug("Response status: %s", response.status_code)

        try:
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, json.decoder.JSONDecodeError) as err:
            logger.error("Request failed. Error: %s", err)
            return None

        return data
