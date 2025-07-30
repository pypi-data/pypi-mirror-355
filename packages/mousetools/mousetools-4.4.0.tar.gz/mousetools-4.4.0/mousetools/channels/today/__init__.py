import logging
from datetime import datetime
from typing import Optional

from dateutil.parser import isoparse

from mousetools.channels import CouchbaseChannel, CouchbaseChildChannel
from mousetools.decorators import disney_property
from mousetools.enums import EntityType

logger = logging.getLogger(__name__)


class TodayChildChannel(CouchbaseChildChannel):
    def __init__(
        self,
        channel_id: str,
        lazy_load: bool = True,
    ) -> None:
        """
        Args:
            channel_id (str): Calendar Channel ID
            lazy_load (bool, optional): If True, will not pull data until a method or property is called. Defaults to True.
        """
        super().__init__(channel_id, lazy_load=lazy_load)

        self.entity_type = EntityType(channel_id.rsplit(".")[-1])

    @disney_property()
    def all_facility_schedules(self) -> Optional[dict[str, list[dict]]]:
        """The list of facility schedules.

        Returns:
            (Optional[dict[str, list[dict]]]): The list of facility schedules, or None if no such data exists.
        """
        return self._cb_data["facilities"]

    def get_schedule(self, entity_id: str) -> list[dict]:
        """Get the schedule info for the given entity

        Args:
            entity_id (str): entity id of the facility

        Returns:
            (list[dict]): schedules
        """
        schedules = []
        if self.all_facility_schedules:
            facility = self.all_facility_schedules.get(entity_id, [])
            for i in facility:
                tmp = {}
                tmp["start"] = isoparse(i["startTime"]).astimezone(self._tz.value)
                tmp["end"] = isoparse(i["endTime"]).astimezone(self._tz.value)
                tmp["schedule_type"] = i["scheduleType"]
                tmp["is_closed"] = i["isClosed"]
                schedules.append(tmp)
        return sorted(schedules, key=lambda i: i["start"])

    def get_open_close_hours(self, entity_id: str) -> tuple[datetime, None]:
        """Get the earliest open and latest close times for an entity.

        This is the entire operating time and ignores the inbetween schedule types like "Early Entry".

        Args:
            entity_id (str): entity id of the facility

        Returns:
            tuple[datetime, None]: A tuple where the 0 index is the opening time and the 1st index is the closing time. Will return None if it could not be found.
        """

        opening = None
        closing = None

        schedules = self.get_schedule(entity_id)
        for i in schedules:
            if opening is None or i["start"] < opening:
                opening = i["start"]

            if closing is None or i["end"] > closing:
                closing = i["end"]

        return opening, closing

    def __repr__(self) -> str:
        return f"TodayChildChannel(channel_id='{self.channel_id}')"


class TodayChannel(CouchbaseChannel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_children_channels(self) -> list[TodayChildChannel]:
        """Get the list of children channels.

        Returns:
            list[TodayChildChannel]: A list of TodayChildChannels
        """
        self.refresh()
        children = []
        for i in self._cb_data.get("results", []):
            if not i["id"].startswith(f"{self.channel_id}."):
                continue
            children.append(TodayChildChannel(i["id"]))

        return children

    def get_entity(self, entity_type: EntityType) -> Optional[TodayChildChannel]:
        """Get the TodayChildChannel for the given entity type

        Args:
            entity_type (EntityType): Entity type to search for

        Returns:
            Optional[TodayChildChannel]: The child channel of the entity or None if it doesn't exist.
        """
        self.refresh()
        check_for = f"{self.channel_id}.{entity_type.value}"
        logger.debug("Check for value: %s", check_for)
        for i in self._cb_data.get("results", []):
            if check_for == i["id"]:
                return TodayChildChannel(i["id"])
