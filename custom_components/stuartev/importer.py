"""
Stuart Energy Importer.

Module handles the import of energy statistics from Stuart Energy into Home Assistant.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING, Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    statistics_during_period,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import EnergyConverter

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.components.recorder.models import StatisticData
    from homeassistant.core import HomeAssistant


class StuartEnergyImporter:
    """Handles formatting and submitting statistics for Stuart Energy."""

    def __init__(
        self,
        hass: HomeAssistant,
        site_info: dict[str, Any],
        statistic_id: str,
    ) -> None:
        """
        Initialize the importer.

        :param hass: Home Assistant instance
        :param site_info: Site information dict
        :param statistic_id: Precomputed valid statistic ID
        """
        self.hass = hass
        self.site_info = site_info
        self.statistic_id = statistic_id

    async def import_segments(self, segments: list[dict[str, Any]]) -> datetime | None:
        """Convert energy segments into hourly statistics and push to recorder."""
        if not segments:
            LOGGER.warning("No energy segments available to import.")
            return None

        timezone = self.hass.config.time_zone
        tzinfo = dt_util.get_time_zone(timezone)

        hourly_data = defaultdict(float)
        for entry in segments:
            timestamp = dt_util.parse_datetime(entry["dateTimeLocal"])
            if timestamp is None:
                continue
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=tzinfo)

            hour_start = timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_data[hour_start] += round(entry["energyGeneratedKwh"], 5)

        if not hourly_data:
            LOGGER.info("No valid hourly data aggregated from segments.")
            return None

        first_hour = min(hourly_data)
        cumulative_sum = await self._async_get_starting_sum(first_hour)

        statistics_list: list[StatisticData] = []
        for hour_start, total_kwh in sorted(hourly_data.items()):
            cumulative_sum += total_kwh
            stat: StatisticData = {
                "start": hour_start,
                "state": total_kwh,
                "sum": cumulative_sum,
            }
            statistics_list.append(stat)

        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=f"{self.site_info.get('name', 'Stuart Site')} Energy Generated",
            source=DOMAIN,
            statistic_id=self.statistic_id,
            unit_class=EnergyConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        )

        async_add_external_statistics(self.hass, metadata, statistics_list)
        LOGGER.debug(
            "Imported %d hourly statistics for site '%s' (%s)",
            len(statistics_list),
            self.site_info.get("name"),
            self.statistic_id,
        )

        return statistics_list[-1]["start"] if statistics_list else None

    async def _async_get_starting_sum(self, start_time: datetime) -> float:
        """Get the last recorder sum before the import window starts."""
        window_start = start_time - timedelta(hours=1)
        current_stats = await get_instance(self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            window_start,
            window_start + timedelta(seconds=1),
            {self.statistic_id},
            "hour",
            None,
            {"sum"},
        )

        if current_stat_rows := current_stats.get(self.statistic_id):
            statistic_sum = current_stat_rows[0].get("sum")
            if isinstance(statistic_sum, int | float):
                return float(statistic_sum)

        last_stat = await get_instance(self.hass).async_add_executor_job(
            partial(
                get_last_statistics,
                self.hass,
                1,
                self.statistic_id,
                convert_units=True,
                types={"sum"},
            )
        )
        if (
            last_stat
            and self.statistic_id in last_stat
            and last_stat[self.statistic_id]
            and last_stat[self.statistic_id][0]["start"] < start_time.timestamp()
        ):
            statistic_sum = last_stat[self.statistic_id][0].get("sum")
            if isinstance(statistic_sum, int | float):
                return float(statistic_sum)

        return 0.0
