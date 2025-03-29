from datetime import timedelta, datetime, UTC
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.recorder.statistics import async_add_external_statistics, get_last_statistics
from homeassistant.util import dt as dt_util
from .const import LOGGER, DOMAIN, SCAN_INTERVAL
from .api import StuartEnergyClient

class StuartEnergyCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client: StuartEnergyClient):
        self.client = client
        self.hass = hass

        super().__init__(
            hass,
            LOGGER,
            name="Stuart Energy Data",
            update_interval=timedelta(hours=SCAN_INTERVAL),
        )

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

                # Get the last recorded timestamp to avoid duplicate submissions
                last_stats = get_last_statistics(self.hass, 1, statistic_id, include_sum=True)
                last_recorded_time = None
                if last_stats and statistic_id in last_stats:
                    last_recorded_time_raw = last_stats[statistic_id][0]["start"]
                    if isinstance(last_recorded_time_raw, float):
                        last_recorded_time = datetime.fromtimestamp(last_recorded_time_raw, UTC)
                    elif isinstance(last_recorded_time_raw, datetime):
                        last_recorded_time = last_recorded_time_raw

                # Compare only the last available timestamp in HA to the last in our dataset
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
