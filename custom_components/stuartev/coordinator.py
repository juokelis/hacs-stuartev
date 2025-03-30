"""
Coordinator for Stuart Energy integration.

Handles data fetching and coordination for sensor updates and statistics import.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import StuartEnergyApiClient, StuartEnergyApiClientCommunicationError
from .const import DOMAIN, LOGGER, SCAN_INTERVAL_DEFAULT

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


class StuartEnergyCoordinator(DataUpdateCoordinator):
    """Coordinator class for Stuart Energy data updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                hours=entry.data.get("scan_interval", SCAN_INTERVAL_DEFAULT)
            ),
        )
        self.entry = entry
        self.hass = hass
        self.api = StuartEnergyApiClient(
            hass,
            entry.data["email"],
            entry.data["password"],
            entry.data["site_id"],
        )
        self.last_processed_time: datetime | None = None

    def _raise_update_failed_error(self, err: Exception) -> None:
        """Raise an error update failed."""
        message = "Failed to fetch data: " + str(err)
        LOGGER.error(message)
        raise UpdateFailed(message) from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest energy data and site info."""
        try:
            return await self._fetch_data_with_retries()
        except StuartEnergyApiClientCommunicationError as err:
            self._raise_update_failed_error(err)

        return {}

    async def _fetch_data_with_retries(self, retries: int = 3) -> dict[str, Any]:
        """Fetch data with retries in case of temporary failures."""
        for attempt in range(retries):
            try:
                return await self._fetch_data()
            except StuartEnergyApiClientCommunicationError:
                if attempt < retries - 1:
                    LOGGER.warning(
                        "Temporary failure, retrying... (%d/%d)", attempt + 1, retries
                    )
                    await asyncio.sleep(2**attempt)
                else:
                    raise
        return {}

    async def _fetch_data(self) -> dict[str, Any]:
        """Actual data fetching logic."""
        now = dt_util.now()
        yesterday = now - timedelta(days=1)

        # Skip if we already processed yesterday
        if (
            self.last_processed_time
            and self.last_processed_time.date() >= yesterday.date()
        ):
            LOGGER.debug("Data for yesterday already processed. Skipping API call.")
            return self.data or {}

        energy_data = await self.api.async_get_energy_data(
            date_from=yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat(),
            date_to=now.isoformat(),
            aggregate_type="QuarterHour",
        )
        site_info = await self.api.async_get_site_info()

        total = energy_data.get("totalGeneratedKwh", 0.0)
        co2 = energy_data.get("co2ReducedKg", 0.0)

        updated = await self._store_statistics(energy_data, site_info)
        if updated:
            # Set last processed time to last segment timestamp
            segments = energy_data.get("energyGeneratedSegments", [])
            if segments:
                last_segment_time = datetime.fromisoformat(
                    segments[-1]["dateTimeLocal"]
                ).replace(tzinfo=UTC)
                self.last_processed_time = last_segment_time
                LOGGER.info(
                    "Stored %d new segments. Last segment time: %s",
                    len(segments),
                    last_segment_time.isoformat(),
                )

        return {
            "site": site_info,
            "total": total,
            "co2": co2,
        }

    async def _store_statistics(
        self, energy_data: dict[str, Any], site_info: dict[str, Any]
    ) -> bool:
        """Store external statistics from 15-minute interval data."""
        if not (segments := energy_data.get("energyGeneratedSegments")):
            LOGGER.warning("No energy segments found in data.")
            return False

        new_stats = []
        for segment in segments:
            timestamp = datetime.fromisoformat(segment["dateTimeLocal"]).replace(
                tzinfo=UTC
            )
            new_stats.append(
                {
                    "start": timestamp,
                    "state": round(segment["energyGeneratedKwh"], 5),
                    "sum": None,
                }
            )

        if new_stats:
            site_id = site_info.get("id")
            object_id = site_info.get("objectId")
            stat_id = f"sensor.stuart_energy_{site_id}_{object_id}"

            async_add_external_statistics(
                self.hass,
                metadata={
                    "has_mean": False,
                    "has_sum": False,
                    "name": f"{site_info.get('name', 'Stuart Site')} Energy Generated",
                    "source": DOMAIN,
                    "statistic_id": stat_id,
                    "unit_of_measurement": "kWh",
                },
                statistics=new_stats,
            )
            LOGGER.debug(
                "Submitted %d new statistics to recorder for site '%s' (%s).",
                len(new_stats),
                site_info.get("name"),
                stat_id,
            )
            return True

        LOGGER.info("No new statistics to store.")
        return False

    async def import_historical_data(self, days: int) -> None:
        """Import historical statistics for the last N days."""
        end = dt_util.now()
        for i in range(days):
            day = end - timedelta(days=i + 1)
            energy_data = await self.api.async_get_energy_data(
                date_from=day.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).isoformat(),
                date_to=day.replace(
                    hour=23, minute=59, second=59, microsecond=0
                ).isoformat(),
                aggregate_type="QuarterHour",
            )
            site_info = await self.api.async_get_site_info()
            await self._store_statistics(energy_data, site_info)
