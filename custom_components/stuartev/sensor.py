from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sensors = [
        StuartEnergySensor(coordinator),
        StuartCO2Sensor(coordinator),
    ]
    async_add_entities(sensors)


class StuartEnergySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "stuart_energy_generated"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def name(self):
        return f"{self.site_name} Energy Generated"

    @property
    def site_name(self):
        site = self.coordinator.data.get("site")
        return site.get("name") if site else "Stuart Site"

    @property
    def native_value(self):
        return round(self.coordinator.data.get("total", 0.0), 3)


class StuartCO2Sensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "stuart_co2_reduced"
        self._attr_native_unit_of_measurement = "kg"
        self._attr_device_class = SensorDeviceClass.CO2
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"{self.site_name} CO2 Reduced"

    @property
    def site_name(self):
        site = self.coordinator.data.get("site")
        return site.get("name") if site else "Stuart Site"

    @property
    def native_value(self):
        data = self.coordinator.data.get("energy")
        if data and "co2ReducedKg" in data:
            return round(data["co2ReducedKg"], 2)
        return None
