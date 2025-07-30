import logging

from dateutil.parser import isoparse

from mousetools.channels import CouchbaseChannel, CouchbaseChildChannel
from mousetools.channels.enums import CouchbaseChannels

logger = logging.getLogger(__name__)


class ForecastedWaitTimesChildChannel(CouchbaseChildChannel):
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

    def get_forecast(self) -> list[dict]:
        """Returns a list of forecasted wait times sorted by timestamp

        Returns:
            (list[dict]): A list of dictionaries. Each dictionary contains forecasted wait minutes, bar graph percentage, accessibility label, and timestamp
        """
        self.refresh()
        try:
            if "forecasts" not in self._cb_data:
                return []

            forecasts = []
            for forecast in self._cb_data["forecasts"]:
                tmp = {}
                dt = isoparse(forecast["timestamp"])
                dt = dt.astimezone(self._tz.value)
                tmp["forecasted_wait_minutes"] = forecast["forecastedWaitMinutes"]
                tmp["bar_graph_percentage"] = forecast["percentage"]
                tmp["accessibility_label"] = forecast["accessibility12h"].split(" ", 1)[-1]
                tmp["timestamp"] = dt
                forecasts.append(tmp)

            return sorted(forecasts, key=lambda i: i["timestamp"])

        except (KeyError, TypeError, ValueError):
            logger.debug("No forecast found for %s", self.channel_id)
            return []


class ForecastedWaitTimesChannel(CouchbaseChannel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_children_channels(self) -> list[ForecastedWaitTimesChildChannel]:
        """Gets a list of children channels for the channel.

        Returns:
            (list[ForecastedWaitTimesChildChannel]): A list of ForecastedWaitTimesChildChannel
        """
        self.refresh()
        channels = []
        for i in self._cb_data["results"]:
            if CouchbaseChannels.FORECASTED_WAIT_TIMES in i["id"]:
                channels.append(ForecastedWaitTimesChildChannel(i["id"]))
        return channels
