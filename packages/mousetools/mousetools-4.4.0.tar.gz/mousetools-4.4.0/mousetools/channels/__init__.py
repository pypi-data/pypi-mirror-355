import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Union

from dateutil.parser import isoparse

from mousetools.channels.enums import DestinationTimezones, DLRCouchbaseChannels, WDWCouchbaseChannels
from mousetools.decorators import disney_property
from mousetools.enums import DestinationShort, EntityType
from mousetools.mixins.couchbase import CouchbaseMixin

logger = logging.getLogger(__name__)


class CouchbaseChildChannel(CouchbaseMixin):
    def __init__(self, channel_id: str, lazy_load: bool = True) -> None:
        if isinstance(channel_id, Enum):
            channel_id = channel_id.value

        self.channel_id: str = channel_id
        self.entity_id: str = channel_id.rsplit(".", 1)[-1]

        self._destination_short: DestinationShort = self.channel_id.split(".")[0]
        self._tz: DestinationTimezones = (
            DestinationTimezones.WALT_DISNEY_WORLD
            if self._destination_short == DestinationShort.WALT_DISNEY_WORLD
            else DestinationTimezones.DISNEYLAND_RESORT
        )
        self._refresh_interval: timedelta = timedelta(hours=12)
        self._cb_data: Optional[dict] = None
        self._cb_data_pull_time: datetime = datetime.now(tz=self._tz.value)
        if not lazy_load:
            self.refresh()

    def refresh(self) -> None:
        """Pulls initial data if none exists or if it is older than the refresh interval"""

        no_data_check = self._cb_data is None
        time_since_pull = datetime.now(tz=self._tz.value) - self._cb_data_pull_time
        old_data_check = time_since_pull > self._refresh_interval
        logger.debug(
            "No data check: %s, Time since pull: %s, Old data check: %s", no_data_check, time_since_pull, old_data_check
        )
        if no_data_check or old_data_check:
            logger.info("Refreshing %s", self.channel_id)
            self._cb_data = self.get_channel_data(self.channel_id)
            self._cb_data_pull_time = datetime.now(tz=self._tz.value)

    @disney_property()
    def last_update(self) -> Optional[datetime]:
        """
        The last time disney updated the data.

        Returns:
            (Optional[datetime]): The last time the entity's data was updated, or None if no such data exists.
        """
        dt = isoparse(self._cb_data["lastUpdate"])
        dt = dt.replace(tzinfo=self._tz.value)
        return dt


class CouchbaseChannel(CouchbaseMixin):
    def __init__(self, channel_id: Union[WDWCouchbaseChannels, DLRCouchbaseChannels], lazy_load: bool = True) -> None:
        """
        Args:
            channel_id (Union[WDWCouchbaseChannels, DLRCouchbaseChannels]): Channel ID from the enum
            lazy_load (bool, optional): If True, will not pull data until a method or property is called. Defaults to True.
        """
        if isinstance(channel_id, Enum):
            channel_id = channel_id.value
        self.channel_id = channel_id

        self._destination_short: DestinationShort = channel_id.split(".")[0]
        self._tz: DestinationTimezones = (
            DestinationTimezones.WALT_DISNEY_WORLD
            if self._destination_short == DestinationShort.WALT_DISNEY_WORLD
            else DestinationTimezones.DISNEYLAND_RESORT
        )

        self._cb_data = None
        self._refresh_interval = timedelta(minutes=10)
        self._cb_data_pull_time = datetime.now(tz=self._tz.value)

        if not lazy_load:
            self.refresh()

    def refresh(self) -> None:
        """Pulls initial data if none exists or if it is older than the refresh interval"""
        no_data_check = self._cb_data is None
        time_since_pull = datetime.now(tz=self._tz.value) - self._cb_data_pull_time
        old_data_check = time_since_pull > self._refresh_interval
        logger.debug(
            "No data check: %s, Time since last update: %s, Old data check: %s",
            no_data_check,
            time_since_pull,
            old_data_check,
        )
        if no_data_check or old_data_check:
            logger.info("Refreshing %s", self.channel_id)
            self._cb_data = self.get_channel_changes(self.channel_id)
            self._cb_data_pull_time = datetime.now(tz=self._tz.value)

    def get_children_channel_ids(self) -> list[str]:
        """Returns a list of child channel ids for the channel."""
        self.refresh()

        return [i["id"] for i in self._cb_data["results"]]

    def _get_children_objects_helper(
        self, class_obj: CouchbaseChildChannel, entity_type: EntityType
    ) -> list[CouchbaseChildChannel]:
        """Searches through the couchbase data for the given entity type and returns an instanct of the given class obj

        Args:
            class_obj (CouchbaseChildChannel): A reference to a child channel class that will be used to instantiate the object. E.g. FacilitiesChildChannel, FacilityStatusChildChannel. etc.
            entity_type (EntityType): The entity type to look for in the results.

        Returns:
            list[CouchbaseChildChannel]: A list of instantiated objects with the same type as given in class_obj.
        """
        self.refresh()
        channels = []
        check_for = f"entitytype={entity_type.value}".lower()
        for i in self._cb_data["results"]:
            if check_for == i["id"].rsplit(";")[-1].lower():
                channels.append(class_obj(i["id"]))
        return channels

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(channel_id='{self.channel_id}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CouchbaseChannel):
            return self.channel_id == other.channel_id
        return False
