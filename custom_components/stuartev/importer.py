"""
Stuart Energy Importer.

Module handles the import of energy statistics from Stuart Energy into Home Assistant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant

    from .api import StuartEnergyApiClient


class StuartEnergyImporter:
    """Handles formatting and submitting statistics for Stuart Energy."""

    def __init__(self, hass: HomeAssistant, api: StuartEnergyApiClient) -> None:
        """
        Initialize the importer.

        :param hass: Home Assistant instance
        :param api: StuartEnergyApiClient instance
        """
        self.hass = hass
        self.api = api

    async def import_segments(
        self, site_info: dict[str, Any], segments: list[dict[str, Any]]
    ) -> datetime | None:
        """Convert 15-minute segments into external statistics and push to recorder."""
        if not segments:
            LOGGER.warning("No energy segments available to import.")
            return None

        statistics: list[StatisticData] = []
        site_id = site_info.get("id")
        object_id = site_info.get("objectId")
        stat_id = f"sensor.stuart_energy_{site_id}_{object_id}"

        for entry in segments:
            timestamp = dt_util.parse_datetime(entry["dateTimeLocal"])
            if timestamp is None:
                continue

            statistics.append(
                StatisticData(
                    start=timestamp,
                    state=cast("float", round(entry["energyGeneratedKwh"], 5)),
                    sum=None,
                )
            )

        metadata = StatisticMetaData(
            has_mean=False,
            has_sum=False,
            name=f"{site_info.get('name', 'Stuart Site')} Energy Generated",
            source=DOMAIN,
            statistic_id=stat_id,
            unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        )

        async_add_external_statistics(self.hass, metadata, statistics)
        LOGGER.debug(
            "Imported %d statistics for site '%s' (%s)",
            len(statistics),
            site_info.get("name"),
            stat_id,
        )

        return timestamp if statistics else None
