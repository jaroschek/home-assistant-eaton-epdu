"""Support for Eaton ePDU sensors."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SNMP_OID_INPUTS_CURRENT,
    SNMP_OID_INPUTS_FEED_NAME,
    SNMP_OID_INPUTS_VOLTAGE,
    SNMP_OID_INPUTS_WATT_HOURS,
    SNMP_OID_INPUTS_WATTS,
    SNMP_OID_OUTLETS_CURRENT,
    SNMP_OID_OUTLETS_DESIGNATOR,
    SNMP_OID_OUTLETS_WATT_HOURS,
    SNMP_OID_OUTLETS_WATTS,
    SNMP_OID_UNITS_INPUT_COUNT,
    SNMP_OID_UNITS_OUTLET_COUNT,
)
from .coordinator import SnmpCoordinator
from .entity import SnmpEntity

PARALLEL_UPDATES = 0
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensors."""

    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []

    for unit in coordinator.get_units():
        for index in range(
            1,
            coordinator.data.get(SNMP_OID_UNITS_INPUT_COUNT.replace("unit", unit), 0)
            + 1,
        ):
            entities.append(SnmpInputCurrentSensorEntity(coordinator, unit, index))
            entities.append(SnmpInputVoltageSensorEntity(coordinator, unit, index))
            entities.append(SnmpInputWattsSensorEntity(coordinator, unit, index))
            entities.append(SnmpInputWattHoursSensorEntity(coordinator, unit, index))

        for index in range(
            1,
            coordinator.data.get(SNMP_OID_UNITS_OUTLET_COUNT.replace("unit", unit), 0)
            + 1,
        ):
            entities.append(SnmpOutletCurrentSensorEntity(coordinator, unit, index))
            entities.append(SnmpOutletWattsSensorEntity(coordinator, unit, index))
            entities.append(SnmpOutletWattHoursSensorEntity(coordinator, unit, index))

    async_add_entities(entities)


class SnmpSensorEntity(SnmpEntity, SensorEntity):
    """Representation of a Eaton ePDU sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    _name_oid: str | None = None
    _value_oid: str | None = None

    _multiplier: float | None = None

    _name_prefix: str = ""
    _name_suffix: str = ""

    _default_value: float = 0.0

    def __init__(self, coordinator: SnmpCoordinator, unit: str, index: str) -> None:
        """Initialize a Eaton ePDU sensor."""
        super().__init__(coordinator, unit)
        self._name_oid = self._name_oid.replace("unit", unit).replace(
            "index", str(index)
        )
        self._value_oid = self._value_oid.replace("unit", unit).replace(
            "index", str(index)
        )
        device_name = self.device_info["name"]
        sensor_name = self.coordinator.data.get(self._name_oid)
        self._attr_name = (
            f"{device_name} {self._name_prefix} {sensor_name} {self._name_suffix}"
        )
        self._attr_unique_id = f"{DOMAIN}_{self.identifier}_{self._value_oid}"
        self._attr_native_value = self.coordinator.data.get(
            self._value_oid, self._default_value
        )
        if self._multiplier is not None:
            self._attr_native_value *= self._multiplier

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data.get(
            self._value_oid, self._default_value
        )
        if self._multiplier is not None:
            self._attr_native_value *= self._multiplier

        super().async_write_ha_state()


class SnmpInputSensorEntity(SnmpSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input sensor."""

    _name_oid = SNMP_OID_INPUTS_FEED_NAME
    _name_prefix = "Input"


class SnmpInputCurrentSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input current sensor."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    _multiplier = 0.001
    _name_suffix = "Current"
    _value_oid = SNMP_OID_INPUTS_CURRENT


class SnmpInputVoltageSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

    _multiplier = 0.001
    _name_suffix = "Voltage"
    _value_oid = SNMP_OID_INPUTS_VOLTAGE


class SnmpInputWattsSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input watts sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    _name_suffix = "Watts"
    _value_oid = SNMP_OID_INPUTS_WATTS


class SnmpInputWattHoursSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input watt hours sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    _multiplier = 0.001
    _name_suffix = "Kilowatt Hours"
    _value_oid = SNMP_OID_INPUTS_WATT_HOURS


class SnmpOutletSensorEntity(SnmpSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet sensor."""

    _name_oid = SNMP_OID_OUTLETS_DESIGNATOR
    _name_prefix = "Outlet"


class SnmpOutletCurrentSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet current sensor."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_entity_registry_visible_default = False

    _multiplier = 0.001
    _name_suffix = "Current"
    _value_oid = SNMP_OID_OUTLETS_CURRENT


class SnmpOutletWattsSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet watts sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    _name_suffix = "Watts"
    _value_oid = SNMP_OID_OUTLETS_WATTS


class SnmpOutletWattHoursSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet watt hours sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    _multiplier = 0.001
    _name_suffix = "Kilowatt Hours"
    _value_oid = SNMP_OID_OUTLETS_WATT_HOURS
