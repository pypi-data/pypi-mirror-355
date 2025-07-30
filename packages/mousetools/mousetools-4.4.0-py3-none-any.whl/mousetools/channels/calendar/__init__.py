import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from dateutil.parser import isoparse

from mousetools.channels import CouchbaseChannel, CouchbaseChildChannel
from mousetools.channels.enums import CouchbaseChannels
from mousetools.decorators import disney_property

logger = logging.getLogger(__name__)


class CalendarChildChannel(CouchbaseChildChannel):
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(channel_id='{self.channel_id}')"

    @disney_property()
    def calendar_id(self) -> Optional[str]:
        """The ID of the calendar

        Returns:
            (Optional[str]): The ID of the calendar, or None if no such data exists.
        """
        return self._cb_data["id"]

    @disney_property()
    def all_closed(self) -> Optional[list[dict]]:
        """The list of closed facilities.

        Returns:
            (Optional[list[dict]]): The list of closed facilities, or None if no such data exists.
        """
        return self._cb_data["closed"]

    @disney_property()
    def all_facility_schedules(self) -> Optional[dict[str, list[dict]]]:
        """The list of facility schedules.

        Returns:
            (Optional[dict[str, list[dict]]]): The list of facility schedules, or None if no such data exists.
        """
        return self._cb_data["facilitySchedules"]

    @disney_property()
    def all_meal_periods(self) -> Optional[dict[str, list[dict]]]:
        """The list of meal periods.

        Returns:
            (Optional[dict[str, list[dict]]]): The list of meal periods, or None if no such data exists.
        """
        return self._cb_data["mealPeriods"]

    @disney_property()
    def all_park_hours(self) -> Optional[list[dict]]:
        """The list of park hours.

        Returns:
            (Optional[list[dict]]): The list of park hours, or None if no such data exists.
        """
        return self._cb_data["parkHours"]

    @disney_property()
    def all_private_events(self) -> Optional[list[dict]]:
        """The list of private events.

        Returns:
            (Optional[list[dict]]): The list of private events, or None if no such data exists.
        """
        return self._cb_data["privateEvents"]

    @disney_property()
    def all_refurbishments(self) -> Optional[list[dict]]:
        """The list of refurbishments.

        Returns:
            (Optional[list[dict]]): The list of refurbishments, or None if no such data exists.
        """
        return self._cb_data["refurbishments"]

    @property
    def timezone(self) -> ZoneInfo:
        """The timezone of the calendar.

        Returns:
            (ZoneInfo): The timezone of the calendar.
        """
        return self._tz.value

    def get_park_hours(self, entity_id: str) -> dict:
        """Get the park hours for the given entity

        Args:
            entity_id (str): entity id of the facility

        Returns:
            (dict): park hours broken up into their schedule types (Operating, Early Entry, etc.)
        """
        hours = {}
        if self.all_park_hours:
            for i in self.all_park_hours:
                if entity_id in i["facilityId"]:
                    hours[i["scheduleType"]] = {}
                    hours[i["scheduleType"]]["start"] = isoparse(i["startTime"]).astimezone(self._tz.value)
                    hours[i["scheduleType"]]["end"] = isoparse(i["endTime"]).astimezone(self._tz.value)
        return hours

    def get_meal_periods(self, entity_id: str) -> dict:
        """Get the meal periods for the given entity

        Args:
            entity_id (str): entity id of the facility

        Returns:
            (dict): meal periods
        """
        periods = {}
        if self.all_meal_periods:
            restaurant = self.all_meal_periods.get(entity_id, [])
            for i in restaurant:
                meal_period = i["facilityId"]
                periods[meal_period] = {}
                periods[meal_period]["start"] = isoparse(i["startTime"]).astimezone(self._tz.value)
                periods[meal_period]["end"] = isoparse(i["endTime"]).astimezone(self._tz.value)
                periods[meal_period]["schedule_type"] = i["scheduleType"]
        return periods

    def get_refurbishment(self, entity_id: str) -> dict:
        """Get the refurbishment info for the given entity

        Args:
            entity_id (str): entity id of the facility

        Returns:
            (dict): refurbishments
        """
        refurbishments = {}
        if self.all_refurbishments:
            for i in self.all_refurbishments:
                if entity_id in i["facilityId"]:
                    refurbishments["start"] = isoparse(i["startTime"]).astimezone(self._tz.value)
                    refurbishments["end"] = isoparse(i["endTime"]).astimezone(self._tz.value)
        return refurbishments

    def get_closed(self, entity_id: str) -> dict:
        """Get the closed info for the given entity

        Args:
            entity_id (str): entity id of the facility

        Returns:
            (dict): closed
        """
        closed = {}
        if self.all_closed:
            for i in self.all_closed:
                if entity_id in i["facilityId"]:
                    closed["start"] = isoparse(i["startTime"]).astimezone(self._tz.value)
                    closed["end"] = isoparse(i["endTime"]).astimezone(self._tz.value)
        return closed

    def get_facility_schedule(self, entity_id: str) -> list[dict]:
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
                schedules.append(tmp)
        return sorted(schedules, key=lambda i: i["start"])


class CalendarChannel(CouchbaseChannel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.available_calendars = {}
        self.refresh_calendars()

    def refresh_calendars(self) -> None:
        """Refreshes the available calendars."""
        available_calendars = {}
        for i in self.get_children_channels():
            available_calendars[i.entity_id] = i

        self.available_calendars = available_calendars

    def get_children_channels(self) -> list[CalendarChildChannel]:
        """Gets a list of children channels for the channel.

        Returns:
            (list[CalendarChildChannel]): A list of CalendarChildChannel
        """
        self.refresh()
        channels = []
        for i in self._cb_data["results"]:
            if CouchbaseChannels.CALENDAR in i["id"]:
                channels.append(CalendarChildChannel(i["id"]))
        return channels

    def get_calendar(self, day: int, month: int) -> Optional[CalendarChildChannel]:
        """Get the calendar for the given day and month

        Args:
            day (int): day of the month
            month (int): month of the year

        Returns:
            (Optional[CalendarChildChannel]): calendar for the given day and month
        """
        self.refresh_calendars()
        return self.available_calendars.get(f"{day:02}-{month:02}", None)

    def get_today_calendar(self) -> Optional[CalendarChildChannel]:
        """Get the calendar for today

        Returns:
            (Optional[CalendarChildChannel]): calendar for the given day and month
        """
        today = datetime.now(tz=self._tz.value)
        day = today.day
        month = today.month
        return self.get_calendar(day=day, month=month)
