"""
Stuart Energy Importer.

Module handles the import of energy statistics from Stuart Energy into Home Assistant.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from homeassistant.components.recorder.models import StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

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
        """Convert 15-minute segments into external statistics and push to recorder."""
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

        statistics_list: list[StatisticData] = []
        for hour_start, total_kwh in sorted(hourly_data.items()):
            stat: StatisticData = {
                "start": hour_start,
                "state": total_kwh,
            }
            statistics_list.append(stat)

        metadata = StatisticMetaData(
            has_mean=False,
            has_sum=False,
            name=f"{self.site_info.get('name', 'Stuart Site')} Energy Generated",
            source=DOMAIN,
            statistic_id=self.statistic_id,
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
