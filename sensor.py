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
    ELECTRIC_CURRENT_AMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    POWER_WATT,
    ENERGY_KILO_WATT_HOUR,
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
    SNMP_OID_UNITS_PART_NUMBER,
    SNMP_OID_UNITS_SERIAL_NUMBER,
)

from .coordinator import SnmpCoordinator
from .entity import SnmpEntity

PARALLEL_UPDATES = 1
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for index in range(1, coordinator.data.get(SNMP_OID_UNITS_INPUT_COUNT, 0) + 1):
        entities.append(SnmpInputCurrentSensorEntity(coordinator, index))
        entities.append(SnmpInputVoltageSensorEntity(coordinator, index))
        entities.append(SnmpInputWattsSensorEntity(coordinator, index))
        entities.append(SnmpInputWattHoursSensorEntity(coordinator, index))

    for index in range(1, coordinator.data.get(SNMP_OID_UNITS_OUTLET_COUNT, 0) + 1):
        entities.append(SnmpOutletCurrentSensorEntity(coordinator, index))
        entities.append(SnmpOutletWattsSensorEntity(coordinator, index))
        entities.append(SnmpOutletWattHoursSensorEntity(coordinator, index))

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

    def __init__(self, coordinator: SnmpCoordinator) -> None:
        """Initialize a Eaton ePDU sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{self.coordinator.data.get(SNMP_OID_UNITS_PART_NUMBER)} {self._name_prefix} {self.coordinator.data.get(self._name_oid)} {self._name_suffix}"
        self._attr_unique_id = f"{DOMAIN}_{self.coordinator.data.get(SNMP_OID_UNITS_SERIAL_NUMBER)}_{self._value_oid}"
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

    _name_prefix = "Input"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU input sensor."""
        self._name_oid = SNMP_OID_INPUTS_FEED_NAME + str(index)
        super().__init__(coordinator)


class SnmpInputCurrentSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input current sensor."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = ELECTRIC_CURRENT_AMPERE

    _multiplier = 0.001
    _name_suffix = "Current"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU input current sensor."""
        self._value_oid = SNMP_OID_INPUTS_CURRENT + str(index)
        super().__init__(coordinator, index)


class SnmpInputVoltageSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = ELECTRIC_POTENTIAL_VOLT

    _multiplier = 0.001
    _name_suffix = "Voltage"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU input voltage sensor."""
        self._value_oid = SNMP_OID_INPUTS_VOLTAGE + str(index)
        super().__init__(coordinator, index)


class SnmpInputWattsSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input watts sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = POWER_WATT

    _name_suffix = "Watts"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU input watts sensor."""
        self._value_oid = SNMP_OID_INPUTS_WATTS + str(index)
        super().__init__(coordinator, index)


class SnmpInputWattHoursSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input watt hours sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    _multiplier = 0.001
    _name_suffix = "Kilowatt Hours"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU input watt hours sensor."""
        self._value_oid = SNMP_OID_INPUTS_WATT_HOURS + str(index)
        super().__init__(coordinator, index)


class SnmpOutletSensorEntity(SnmpSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet sensor."""

    _name_prefix = "Outlet"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU outlet sensor."""
        self._name_oid = SNMP_OID_OUTLETS_DESIGNATOR + str(index)
        super().__init__(coordinator)


class SnmpOutletCurrentSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet current sensor."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = ELECTRIC_CURRENT_AMPERE
    _attr_entity_registry_visible_default = False

    _multiplier = 0.001
    _name_suffix = "Current"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU outlet current sensor."""
        self._value_oid = SNMP_OID_OUTLETS_CURRENT + str(index)
        super().__init__(coordinator, index)


class SnmpOutletWattsSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet watts sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = POWER_WATT

    _name_suffix = "Watts"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU outlet watts sensor."""
        self._value_oid = SNMP_OID_OUTLETS_WATTS + str(index)
        super().__init__(coordinator, index)


class SnmpOutletWattHoursSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet watt hours sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    _multiplier = 0.001
    _name_suffix = "Kilowatt Hours"

    def __init__(self, coordinator: SnmpCoordinator, index: int) -> None:
        """Initialize a Eaton ePDU outlet watt hours sensor."""
        self._value_oid = SNMP_OID_OUTLETS_WATT_HOURS + str(index)
        super().__init__(coordinator, index)
