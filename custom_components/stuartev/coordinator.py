from datetime import timedelta, datetime, UTC
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.recorder.statistics import async_add_external_statistics, get_last_statistics
from homeassistant.util import dt as dt_util
from .const import LOGGER, DOMAIN
from .api import StuartEnergyClient

class StuartEnergyCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client: StuartEnergyClient, scan_interval: int = 3):
        self.client = client
        self.hass = hass

        super().__init__(
            hass,
            LOGGER,
            name="Stuart Energy Data",
            update_interval=timedelta(hours=scan_interval),
        )

    async def import_historical_data(self, days_back: int):
        statistic_id = "sensor.stuart_energy_generated"
        now = datetime.now(UTC)
        total = 0.0

        for day in range(days_back, 0, -1):
            date_from = (now - timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
            date_to = date_from + timedelta(days=1)

            data = await self.client.async_get_energy_data(date_from.isoformat(), date_to.isoformat())
            if not data or "energyGeneratedSegments" not in data:
                continue

            segments = data["energyGeneratedSegments"]
            if not segments:
                continue

            last_stats = get_last_statistics(self.hass, 1, statistic_id, include_sum=True)
            last_recorded_time = None
            if last_stats and statistic_id in last_stats:
                raw = last_stats[statistic_id][0]["start"]
                last_recorded_time = datetime.fromtimestamp(raw, UTC) if isinstance(raw, float) else raw

            last_segment_time = dt_util.parse_datetime(segments[-1]["dateTimeLocal"])
            if last_recorded_time and last_segment_time <= last_recorded_time:
                continue

            statistics = []
            cumulative = 0.0
            for seg in segments:
                try:
                    start = dt_util.parse_datetime(seg["dateTimeLocal"])
                    value = float(seg["energyGeneratedKwh"])
                    cumulative += value
                    total += value
                    statistics.append({
                        "start": start,
                        "state": value,
                        "sum": cumulative
                    })
                except Exception as e:
                    LOGGER.warning("Skipping invalid segment: %s", e)

            if statistics:
                async_add_external_statistics(
                    self.hass,
                    statistic_id,
                    {
                        "name": "Stuart Energy Generated",
                        "source": DOMAIN,
                        "statistic_id": statistic_id,
                        "unit_of_measurement": "kWh"
                    },
                    statistics
                )

        return total

    async def _async_update_data(self):
        try:
            now = datetime.now(UTC)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today_start - timedelta(days=1)

            data = await self.client.async_get_energy_data(
                date_from=yesterday.isoformat(),
                date_to=now.isoformat()
            )

            site_info = await self.client.async_get_site_info()

            # Store 15-minute segments in long-term statistics database
            statistic_id = "sensor.stuart_energy_generated"
            if data and "energyGeneratedSegments" in data:
                segments = data["energyGeneratedSegments"]
                if not segments:
                    return {"energy": data, "site": site_info, "total": 0.0}

                last_stats = get_last_statistics(self.hass, 1, statistic_id, include_sum=True)
                last_recorded_time = None
                if last_stats and statistic_id in last_stats:
                    raw = last_stats[statistic_id][0]["start"]
                    last_recorded_time = datetime.fromtimestamp(raw, UTC) if isinstance(raw, float) else raw

                last_segment_time = dt_util.parse_datetime(segments[-1]["dateTimeLocal"])
                if last_recorded_time and last_segment_time <= last_recorded_time:
                    LOGGER.debug("No new energy segments to store.")
                    return {"energy": data, "site": site_info, "total": sum(seg["energyGeneratedKwh"] for seg in segments)}

                statistics = []
                cumulative = 0.0
                for seg in segments:
                    try:
                        start = dt_util.parse_datetime(seg["dateTimeLocal"])
                        value = float(seg["energyGeneratedKwh"])
                        cumulative += value
                        statistics.append({
                            "start": start,
                            "state": value,
                            "sum": cumulative
                        })
                    except Exception as e:
                        LOGGER.warning("Skipping invalid segment: %s", e)

                if statistics:
                    async_add_external_statistics(
                        self.hass,
                        statistic_id,
                        {
                            "name": "Stuart Energy Generated",
                            "source": DOMAIN,
                            "statistic_id": statistic_id,
                            "unit_of_measurement": "kWh"
                        },
                        statistics
                    )

                return {
                    "energy": data,
                    "site": site_info,
                    "total": cumulative
                }

            return {
                "energy": data,
                "site": site_info,
                "total": 0.0
            }

        except Exception as err:
            raise UpdateFailed(f"Error updating Stuart data: {err}") from err
