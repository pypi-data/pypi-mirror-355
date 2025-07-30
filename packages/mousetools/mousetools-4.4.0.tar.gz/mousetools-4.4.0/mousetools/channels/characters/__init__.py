import logging
from typing import Optional

from dateutil.parser import isoparse

from mousetools.channels import CouchbaseChannel, CouchbaseChildChannel
from mousetools.channels.enums import CouchbaseChannels
from mousetools.decorators import disney_property

logger = logging.getLogger(__name__)


class CharactersChildChannel(CouchbaseChildChannel):
    def __init__(
        self,
        channel_id: str,
        lazy_load: bool = True,
    ) -> None:
        """
        Args:
            channel_id (str): Forecasted Wait Times Channel ID
            lazy_load (bool, optional): If True, will not pull data until a method or property is called. Defaults to True.
        """
        super().__init__(channel_id, lazy_load=lazy_load)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(channel_id='{self.channel_id}')"

    @disney_property()
    def name(self) -> Optional[str]:
        """The name of the entity.

        Returns:
            (Optional[str]): The name of the entity, or None if it was not found.
        """
        return self._cb_data["name"]

    @disney_property()
    def character_id(self) -> Optional[str]:
        """The character ID of the entity. Strips the region from the channel ID.

        Returns:
            (Optional[str]): The character ID of the entity, or None if it was not found.
        """
        return self._cb_data["characterId"]

    @disney_property()
    def description(self) -> Optional[str]:
        """The description of the entity.

        Returns:
            (Optional[str]): The description of the entity, or None if it was not found.
        """
        return self._cb_data["description"]

    @disney_property()
    def thumbnail_url(self) -> Optional[str]:
        """The thumbnail URL of the entity.

        Returns:
            (Optional[str]): The thumbnail URL of the entity, or None if it was not found.
        """
        return self._cb_data["thumbnailUrl"]

    @disney_property()
    def banner_url(self) -> Optional[str]:
        """The banner URL of the entity.

        Returns:
            (Optional[str]): The banner URL of the entity, or None if it was not found.
        """
        return self._cb_data["bannerUrl"]

    def get_appearances(self) -> list[dict]:
        """The current list of appearances of the character is scheduled for.

        Returns:
            (list[dict]): The list of appearances of the entity.
        """
        self.refresh()
        try:
            if "appearances" not in self._cb_data:
                return []

            _appearances = []
            for i in self._cb_data["appearances"]:
                tmp = {}
                tmp["start_datetime"] = isoparse(i["startDateTime"]).astimezone(self._tz.value)
                tmp["end_datetime"] = isoparse(i["endDateTime"]).astimezone(self._tz.value)
                tmp["start_time_str"] = i["startTime"]
                tmp["end_time_str"] = i["endTime"]
                tmp["coordinates"] = {"latitude": i["latitude"], "longitude": i["longitude"]}
                tmp["facility_id"] = i["facilityId"]
                tmp["location_name"] = i["locationName"]
                tmp["location_id"] = i["locationId"]
                tmp["ancestor_land_id"] = i["ancestorLandId"]
                tmp["ancestor_land_name"] = i["ancestorLandName"]
                _appearances.append(tmp)

            return sorted(_appearances, key=lambda i: i["start_datetime"])

        except (KeyError, TypeError, ValueError):
            logger.debug("No forecast found for %s", self.channel_id)
            return []


class CharactersChannel(CouchbaseChannel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_children_channels(self) -> list[CharactersChildChannel]:
        """Gets a list of children channels for the channel.

        Returns:
            (list[CharactersChildChannel]): A list of CharactersChildChannel
        """
        self.refresh()
        channels = []
        for i in self._cb_data["results"]:
            if CouchbaseChannels.CHARACTERS in i["id"]:
                channels.append(CharactersChildChannel(i["id"]))
        return channels
