"""
Coordinator for Stuart Energy integration.

Handles data fetching and coordination for sensor updates and statistics import.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import StuartEnergyApiClient, StuartEnergyApiClientCommunicationError
from .const import DOMAIN, LOGGER, SCAN_INTERVAL_DEFAULT
from .importer import StuartEnergyImporter

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
        self.statistic_id: str | None = None
        self.site_info: dict[str, Any] = {}

    def _generate_statistic_id(self, site_info: dict[str, Any]) -> str:
        """Generate a valid statistic_id from site details."""
        site_id = site_info.get("id")
        object_id = site_info.get("objectId")
        return f"{DOMAIN}:site_{site_id}_obj_{object_id}_energy"

    def _raise_update_failed_error(self, err: Exception) -> None:
        """Raise an error update failed."""
        message = "Failed to fetch data: " + str(err)
        LOGGER.error(message)
        raise UpdateFailed(message) from err

    async def initialize_site_info(self) -> None:
        """Fetch site info and generate statistic ID once."""
        self.site_info = await self.api.async_get_site_info()
        self.statistic_id = self._generate_statistic_id(self.site_info)

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
            ).strftime("%Y-%m-%dT%H:%M:%S"),
            date_to=now.strftime("%Y-%m-%dT%H:%M:%S"),
        )

        total = energy_data.get("totalGeneratedKwh", 0.0)
        co2 = energy_data.get("co2ReducedKg", 0.0)
        segments = energy_data.get("energyGeneratedSegments", [])

        importer = StuartEnergyImporter(self.hass, self.site_info, self.statistic_id)
        last_time = await importer.import_segments(segments)
        if last_time:
            self.last_processed_time = last_time
            LOGGER.info(
                "Stored %d new segments. Last segment time: %s",
                len(segments),
                last_time.isoformat(),
            )

        return {
            "site": self.site_info,
            "total": total,
            "co2": co2,
        }

    async def import_historical_data(self, days: int) -> None:
        """Import historical statistics for the last N days."""
        end = dt_util.now()
        importer = StuartEnergyImporter(self.hass, self.site_info, self.statistic_id)

        for i in range(days):
            day = end - timedelta(days=i + 1)
            energy_data = await self.api.async_get_energy_data(
                date_from=day.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).strftime("%Y-%m-%dT%H:%M:%S"),
                date_to=day.replace(
                    hour=23, minute=59, second=59, microsecond=0
                ).strftime("%Y-%m-%dT%H:%M:%S"),
            )
            await importer.import_segments(
                energy_data.get("energyGeneratedSegments", [])
            )
