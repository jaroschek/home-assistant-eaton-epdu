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
    ATTR_ACCURATE_POWER,
    DOMAIN,
    SNMP_OID_INPUTS_CURRENT,
    SNMP_OID_INPUTS_FEED_NAME,
    SNMP_OID_INPUTS_PF,
    SNMP_OID_INPUTS_VOLTAGE,
    SNMP_OID_INPUTS_WATT_HOURS,
    SNMP_OID_INPUTS_WATTS,
    SNMP_OID_OUTLETS_CURRENT,
    SNMP_OID_OUTLETS_DESIGNATOR,
    SNMP_OID_OUTLETS_PF,
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
            entities.append(SnmpInputCurrentSensorEntity(coordinator, unit, str(index)))
            entities.append(SnmpInputPFSensorEntity(coordinator, unit, str(index)))
            entities.append(SnmpInputVoltageSensorEntity(coordinator, unit, str(index)))
            if entry.data.get(ATTR_ACCURATE_POWER, False):
                entities.append(
                    SnmpInputVAPhiSensorEntity(coordinator, unit, str(index))
                )
            else:
                entities.append(
                    SnmpInputWattsSensorEntity(coordinator, unit, str(index))
                )
            entities.append(
                SnmpInputWattHoursSensorEntity(coordinator, unit, str(index))
            )

        for index in range(
            1,
            coordinator.data.get(SNMP_OID_UNITS_OUTLET_COUNT.replace("unit", unit), 0)
            + 1,
        ):
            entities.append(
                SnmpOutletCurrentSensorEntity(coordinator, unit, str(index))
            )
            entities.append(SnmpOutletPFSensorEntity(coordinator, unit, str(index)))
            if entry.data.get(ATTR_ACCURATE_POWER, False):
                # TODO: input index is hardwired to first input
                # Issue: ePDU seems to have outputVoltageTable (.1.3.6.1.4.1.534.6.6.7.6.3)
                # missing. This means we need to use voltage from input
                # Could use parent OID (1.3.6.1.4.1.534.6.6.7.6.2.1.3.unit.index.1) and
                # a lot of queries to get group voltage but increases number of queries
                entities.append(
                    SnmpOutputVAPhiSensorEntity(coordinator, unit, str(index), "1")
                )
            else:
                entities.append(
                    SnmpOutletWattsSensorEntity(coordinator, unit, str(index))
                )
            entities.append(
                SnmpOutletWattHoursSensorEntity(coordinator, unit, str(index))
            )

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
        self._name_oid = self._name_oid.replace("unit", unit).replace("index", index)
        self._value_oid = self._value_oid.replace("unit", unit).replace("index", index)
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
    _attr_suggested_display_precision = 3

    _multiplier = 0.001
    _name_suffix = "Current"
    _value_oid = SNMP_OID_INPUTS_CURRENT


class SnmpInputPFSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU input power factor sensor."""

    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = None
    _attr_entity_registry_enabled_default = False
    _attr_suggested_display_precision = 3

    _multiplier = 0.001
    _name_suffix = "Power Factor"
    _value_oid = SNMP_OID_INPUTS_PF


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
    _attr_suggested_display_precision = 3

    _multiplier = 0.001
    _name_suffix = "Current"
    _value_oid = SNMP_OID_OUTLETS_CURRENT


class SnmpOutletPFSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a Eaton ePDU outlet power factor sensor."""

    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = None
    _attr_entity_registry_enabled_default = False
    _attr_suggested_display_precision = 3

    _multiplier = 0.001
    _name_suffix = "Power Factor"
    _value_oid = SNMP_OID_OUTLETS_PF


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


class SnmpInputVAPhiSensorEntity(SnmpEntity, SensorEntity):
    """Takes voltage, current and power factor and generates a power sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_display_precision = 3

    _name_oid = SNMP_OID_INPUTS_FEED_NAME

    _name_prefix: str = "Input"
    _name_suffix: str = "Watts"

    _default_value: float = 0.0

    def __init__(self, coordinator: SnmpCoordinator, unit: str, index: str) -> None:
        """Initialize a Eaton ePDU sensor."""
        super().__init__(coordinator, unit)

        self._index = index

        self._name_oid = self._name_oid.replace("unit", unit).replace("index", index)
        device_name = self.device_info["name"]
        sensor_name = self.coordinator.data.get(self._name_oid)
        self._attr_name = (
            f"{device_name} {self._name_prefix} {sensor_name} {self._name_suffix}"
        )
        self._attr_unique_id = f"{DOMAIN}_{self.identifier}_{self._name_oid}_watts2"
        self._attr_native_value = self.get_value()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_native_value = self.get_value()

        super().async_write_ha_state()

    def get_value(self) -> float:
        """Return calculated value."""
        voltage = self.coordinator.data.get(
            SNMP_OID_INPUTS_VOLTAGE.replace("unit", self._unit).replace(
                "index", self._index
            ),
            0,
        )
        current = self.coordinator.data.get(
            SNMP_OID_INPUTS_CURRENT.replace("unit", self._unit).replace(
                "index", self._index
            ),
            0,
        )
        cosphi = self.coordinator.data.get(
            SNMP_OID_INPUTS_PF.replace("unit", self._unit).replace(
                "index", self._index
            ),
            0,
        )

        return (voltage / 1000.0) * (current / 1000) * (abs(cosphi) / 1000)


class SnmpOutputVAPhiSensorEntity(SnmpEntity, SensorEntity):
    """Takes voltage, current and power factor and generates a power sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_display_precision = 3

    _name_oid = SNMP_OID_OUTLETS_DESIGNATOR

    _name_prefix: str = "Outlet"
    _name_suffix: str = "Watts"

    _default_value: float = 0.0

    def __init__(
        self, coordinator: SnmpCoordinator, unit: str, index: str, input_index: str
    ) -> None:
        """Initialize a Eaton ePDU sensor."""
        super().__init__(coordinator, unit)

        self._index = index
        self._input_index = input_index

        self._name_oid = self._name_oid.replace("unit", unit).replace("index", index)
        device_name = self.device_info["name"]
        sensor_name = self.coordinator.data.get(self._name_oid)
        self._attr_name = (
            f"{device_name} {self._name_prefix} {sensor_name} {self._name_suffix}"
        )
        self._attr_unique_id = f"{DOMAIN}_{self.identifier}_{self._name_oid}_watts2"
        self._attr_native_value = self.get_value()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_native_value = self.get_value()

        super().async_write_ha_state()

    def get_value(self) -> float:
        """Return calculated value."""
        voltage = self.coordinator.data.get(
            SNMP_OID_INPUTS_VOLTAGE.replace("unit", self._unit).replace(
                "index", self._input_index
            ),
            0,
        )
        current = self.coordinator.data.get(
            SNMP_OID_OUTLETS_CURRENT.replace("unit", self._unit).replace(
                "index", self._index
            ),
            0,
        )
        cosphi = self.coordinator.data.get(
            SNMP_OID_OUTLETS_PF.replace("unit", self._unit).replace(
                "index", self._index
            ),
            0,
        )

        return (voltage / 1000.0) * (current / 1000) * (abs(cosphi) / 1000)
