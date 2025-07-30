import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from dateutil.parser import isoparse

from mousetools.channels import CouchbaseChannel, CouchbaseChildChannel
from mousetools.channels.enums import CouchbaseChannels
from mousetools.decorators import disney_property
from mousetools.enums import EntityType

logger = logging.getLogger(__name__)


class FacilityStatusChildChannel(CouchbaseChildChannel):
    def __init__(self, channel_id: str, lazy_load: bool = True) -> None:
        """
        Args:
            channel_id (Union[WDWCouchbaseChannels, DLRCouchbaseChannels]): Channel ID from the enum
            lazy_load (bool, optional): If True, will not pull data until a method or property is called. Defaults to True.
        """
        super().__init__(channel_id, lazy_load=lazy_load)

        self._refresh_interval: timedelta = timedelta(minutes=10)

    def get_status(self) -> Optional[str]:
        """Get the operating status of the facility

        Returns:
            (Optional[str]): Operating status. Typically "Operating" or "Closed".
        """
        self.refresh()

        try:
            return self._cb_data["status"]
        except (KeyError, TypeError, ValueError):
            logger.debug("No status found for %s", self.channel_id)
            return None

    def get_wait_time(self) -> Optional[int]:
        """Get the wait time in minutes

        Returns:
            (Optional[int]): Wait time in minutes
        """
        self.refresh()

        try:
            return self._cb_data["waitMinutes"]
        except (KeyError, TypeError, ValueError):
            logger.debug("No wait time found for %s", self.channel_id)
            return None

    @disney_property()
    def fast_pass_available(self) -> Optional[bool]:
        """Whether fast pass is available.

        Returns:
            Optional[bool]: Whether fast pass is available
        """
        return self._cb_data["fastPassAvailable"]

    def get_fast_pass_end_time(self) -> Optional[datetime]:
        """Get the end time of the fast pass

        Returns:
            (Optional[datetime]): End time
        """
        self.refresh()
        try:
            dt = isoparse(self._cb_data["fastPassEndTime"])
            dt = dt.replace(tzinfo=self._tz.value)
            return dt
        except (KeyError, TypeError, ValueError):
            logger.debug("No fast pass end time found for %s", self.channel_id)
            return None

    def get_fast_pass_start_time(self) -> Optional[datetime]:
        """Get the start time of the fast pass

        Returns:
            (Optional[datetime]): Start time
        """
        self.refresh()
        try:
            dt = isoparse(self._cb_data["fastPassStartTime"])
            dt = dt.replace(tzinfo=self._tz.value)
            return dt
        except (KeyError, TypeError, ValueError):
            logger.debug("No fast pass start time found for %s", self.channel_id)
            return None

    @disney_property()
    def single_rider(self) -> Optional[bool]:
        """Whether the facility allows single riders

        Returns:
            (Optional[bool]): Whether the facility allows single riders
        """
        return self._cb_data["singleRider"]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(channel_id='{self.channel_id}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, FacilityStatusChildChannel):
            return self.channel_id == other.channel_id
        return False


AttractionFacilityStatusChild = type("AttractionFacilityStatusChild", (FacilityStatusChildChannel,), {})
EntertainmentFacilityStatusChild = type("EntertainmentFacilityStatusChild", (FacilityStatusChildChannel,), {})
EntertainmentVenueFacilityStatusChild = type("EntertainmentVenueFacilityStatusChild", (FacilityStatusChildChannel,), {})
LandFacilityStatusChild = type("LandFacilityStatusChild", (FacilityStatusChildChannel,), {})
RestaurantFacilityStatusChild = type("RestaurantFacilityStatusChild", (FacilityStatusChildChannel,), {})
ThemeParkFacilityStatusChild = type("ThemeParkFacilityStatusChild", (FacilityStatusChildChannel,), {})
WaterParkFacilityStatusChild = type("WaterParkFacilityStatusChild", (FacilityStatusChildChannel,), {})


class FacilityStatusChannel(CouchbaseChannel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_children_channels(self) -> list[FacilityStatusChildChannel]:
        """Gets a list of children channels for the channel.

        Returns:
            list[FacilityStatusChildChannel]: A list of FacilityStatusChildChannels
        """
        self.refresh()
        channels = []
        for i in self._cb_data["results"]:
            if CouchbaseChannels.FACILITY_STATUS in i["id"]:
                channels.append(FacilityStatusChildChannel(i["id"]))
        return channels

    def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """Get all statuses for the channel

        Returns:
            (dict[str, dict[str, Any]]): A dictionary of all statuses for the channel
        """
        logger.info("Getting all children statuses for %s", self.channel_id)
        children = self.get_children_channels()
        logger.debug("Got %d children for %s", len(children), self.channel_id)

        statuses = {}
        for child in children:
            tmp = {}
            tmp["status"] = child.get_status()
            tmp["wait_time"] = child.get_wait_time()
            statuses[child.entity_id] = tmp

        return statuses

    def get_children_attractions(self) -> list[AttractionFacilityStatusChild]:  # type: ignore
        """Get AttractionFacilityStatusChild Children of a Facility

        Returns:
            list[AttractionFacilityStatusChild]: A list of AttractionFacilityStatusChild Children
        """
        return self._get_children_objects_helper(AttractionFacilityStatusChild, EntityType.ATTRACTION)

    def get_children_entertainment(self) -> list[EntertainmentFacilityStatusChild]:  # type: ignore
        """Get EntertainmentFacilityStatusChild Children of a Facility

        Returns:
            list[EntertainmentFacilityStatusChild]: A list of EntertainmentFacilityStatusChild Children
        """
        return self._get_children_objects_helper(EntertainmentFacilityStatusChild, EntityType.ENTERTAINMENT)

    def get_children_entertainment_venues(self) -> list[EntertainmentVenueFacilityStatusChild]:  # type: ignore
        """Get EntertainmentVenueFacilityStatusChild Children of a Facility

        Returns:
            list[EntertainmentVenueFacilityStatusChild]: A list of EntertainmentVenueFacilityStatusChild Children
        """
        return self._get_children_objects_helper(EntertainmentVenueFacilityStatusChild, EntityType.ENTERTAINMENT_VENUE)

    def get_children_lands(self) -> list[LandFacilityStatusChild]:  # type: ignore
        """Get LandFacilityStatusChild Children of a Facility

        Returns:
            list[LandFacilityStatusChild]: A list of LandFacilityStatusChild Children
        """
        return self._get_children_objects_helper(LandFacilityStatusChild, EntityType.LAND)

    def get_children_restaurants(self) -> list[RestaurantFacilityStatusChild]:  # type: ignore
        """Get RestaurantFacilityStatusChild Children of a Facility

        Returns:
            list[RestaurantFacilityStatusChild]: A list of RestaurantFacilityStatusChild Children
        """
        return self._get_children_objects_helper(RestaurantFacilityStatusChild, EntityType.RESTAURANT)

    def get_children_theme_parks(self) -> list[ThemeParkFacilityStatusChild]:  # type: ignore
        """Get ThemeParkFacilityStatusChild Children of a Facility

        Returns:
            list[ThemeParkFacilityStatusChild]: A list of ThemeParkFacilityStatusChild Children
        """
        return self._get_children_objects_helper(ThemeParkFacilityStatusChild, EntityType.THEME_PARK)

    def get_children_water_parks(self) -> list[WaterParkFacilityStatusChild]:  # type: ignore
        """Get WaterParkFacilityStatusChild Children of a Facility

        Returns:
            list[WaterParkFacilityStatusChild]: A list of WaterParkFacilityStatusChild Children
        """
        return self._get_children_objects_helper(WaterParkFacilityStatusChild, EntityType.WATER_PARK)
