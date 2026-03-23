"""MyFuelPortal sensors."""
import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    RestoreSensor,
)
from homeassistant.const import UnitOfVolume
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for tank in coordinator.data.get("tanks", []):
        name = tank["name"]
        entities.extend([
            TankGallonsSensor(coordinator, entry, name),
            TankPercentSensor(coordinator, entry, name),
            TankCapacitySensor(coordinator, entry, name),
            TankLastDeliverySensor(coordinator, entry, name),
            TankReadingDateSensor(coordinator, entry, name),
            TankDailyUsageSensor(coordinator, entry, name),
            TankCumulativeUsageSensor(coordinator, entry, name),
        ])
    async_add_entities(entities)


def _device_info(entry, tank_name):
    return {
        "identifiers": {(DOMAIN, f"{entry.entry_id}_{tank_name}")},
        "name": f"Propane Tank: {tank_name}",
        "manufacturer": "MyFuelPortal",
        "model": "Monitored Tank",
    }


def _tank_data(coordinator, tank_name):
    for t in coordinator.data.get("tanks", []):
        if t["name"] == tank_name:
            return t
    return {}


class _TankSensorBase(CoordinatorEntity, SensorEntity):
    """Base for all tank sensors."""

    def __init__(self, coordinator, entry, tank_name, key):
        super().__init__(coordinator)
        self._entry = entry
        self._tank_name = tank_name
        self._key = key
        slug = tank_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{slug}_{key}"
        self._attr_has_entity_name = True

    @property
    def device_info(self):
        return _device_info(self._entry, self._tank_name)


class TankGallonsSensor(_TankSensorBase):
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:propane-tank"

    def __init__(self, coordinator, entry, tank_name):
        super().__init__(coordinator, entry, tank_name, "gallons")
        self._attr_name = "Gallons"

    @property
    def native_value(self):
        return _tank_data(self.coordinator, self._tank_name).get("gallons")


class TankPercentSensor(_TankSensorBase):
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator, entry, tank_name):
        super().__init__(coordinator, entry, tank_name, "percent")
        self._attr_name = "Level"

    @property
    def native_value(self):
        return _tank_data(self.coordinator, self._tank_name).get("percent")


class TankCapacitySensor(_TankSensorBase):
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_icon = "mdi:propane-tank-outline"

    def __init__(self, coordinator, entry, tank_name):
        super().__init__(coordinator, entry, tank_name, "capacity")
        self._attr_name = "Capacity"

    @property
    def native_value(self):
        return _tank_data(self.coordinator, self._tank_name).get("capacity")


class TankLastDeliverySensor(_TankSensorBase):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:truck-delivery"

    def __init__(self, coordinator, entry, tank_name):
        super().__init__(coordinator, entry, tank_name, "last_delivery")
        self._attr_name = "Last Delivery"

    @property
    def native_value(self):
        val = _tank_data(self.coordinator, self._tank_name).get("last_delivery")
        if val:
            try:
                return datetime.fromisoformat(val).date()
            except (ValueError, TypeError):
                pass
        return None


class TankReadingDateSensor(_TankSensorBase):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry, tank_name):
        super().__init__(coordinator, entry, tank_name, "reading_date")
        self._attr_name = "Reading Date"

    @property
    def native_value(self):
        val = _tank_data(self.coordinator, self._tank_name).get("reading_date")
        if val:
            try:
                return datetime.fromisoformat(val).date()
            except (ValueError, TypeError):
                pass
        return None


class TankDailyUsageSensor(_TankSensorBase):
    """Estimated gallons/day between readings."""

    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fire"

    def __init__(self, coordinator, entry, tank_name):
        super().__init__(coordinator, entry, tank_name, "daily_usage")
        self._attr_name = "Daily Usage"
        self._prev_gallons = None
        self._prev_date = None

    @property
    def native_value(self):
        tank = _tank_data(self.coordinator, self._tank_name)
        gallons = tank.get("gallons")
        reading = tank.get("reading_date")
        if gallons is None or reading is None:
            return None
        try:
            curr_date = datetime.fromisoformat(reading).date()
        except (ValueError, TypeError):
            return None

        usage = None
        if self._prev_gallons is not None and self._prev_date is not None:
            days = (curr_date - self._prev_date).days
            if days > 0 and self._prev_gallons > gallons:
                usage = round((self._prev_gallons - gallons) / days, 2)

        self._prev_gallons = gallons
        self._prev_date = curr_date
        return usage


class TankCumulativeUsageSensor(CoordinatorEntity, RestoreSensor):
    """Total gallons consumed — for HA Energy dashboard Gas section."""

    _attr_device_class = SensorDeviceClass.GAS
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_FEET
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator, entry, tank_name):
        super().__init__(coordinator)
        self._entry = entry
        self._tank_name = tank_name
        self._last_level = None
        self._total = 0.0
        slug = tank_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{slug}_cumulative_usage"
        self._attr_has_entity_name = True
        self._attr_name = "Cumulative Usage"

    @property
    def device_info(self):
        return _device_info(self._entry, self._tank_name)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_sensor_data()
        if last and last.native_value is not None:
            try:
                self._total = float(last.native_value)
            except (ValueError, TypeError):
                pass
        self._attr_native_value = round(self._total, 2)

    @callback
    def _handle_coordinator_update(self):
        tank = _tank_data(self.coordinator, self._tank_name)
        current = tank.get("gallons")
        if current is None:
            return
        if self._last_level is not None and current < self._last_level:
            used_gallons = self._last_level - current
            self._total += used_gallons * 0.133681  # gallons to ft³
        self._last_level = current
        self._attr_native_value = round(self._total, 2)
        self.async_write_ha_state()
