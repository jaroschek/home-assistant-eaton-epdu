"""Support for SNMP ePDU sensors."""
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
    ENERGY_WATT_HOUR,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SNMP_API_CLIENT,
    SNMP_OID_INPUTS_CURRENT,
    SNMP_OID_INPUTS_FEED_NAME,
    SNMP_OID_INPUTS_VOLTAGE,
    SNMP_OID_INPUTS_WATT_HOURS,
    SNMP_OID_INPUTS_WATTS,
    SNMP_OID_OUTLETS_CURRENT,
    SNMP_OID_OUTLETS_DESIGNATOR,
    SNMP_OID_OUTLETS_VOLTAGE,
    SNMP_OID_OUTLETS_WATT_HOURS,
    SNMP_OID_OUTLETS_WATTS,
    SNMP_OID_UNITS_FIRMWARE_VERSION,
    SNMP_OID_UNITS_INPUT_COUNT,
    SNMP_OID_UNITS_OUTLET_COUNT,
    SNMP_OID_UNITS_PART_NUMBER,
    SNMP_OID_UNITS_PRODUCT_NAME,
    SNMP_OID_UNITS_SERIAL_NUMBER,
)

from .api import SnmpApi
from .entity import SnmpEntity

PARALLEL_UPDATES = 1
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensors."""

    api = hass.data[DOMAIN][entry.entry_id][SNMP_API_CLIENT]
    device = api.get(
        [
            SNMP_OID_UNITS_PRODUCT_NAME,
            SNMP_OID_UNITS_PART_NUMBER,
            SNMP_OID_UNITS_SERIAL_NUMBER,
            SNMP_OID_UNITS_FIRMWARE_VERSION,
            SNMP_OID_UNITS_INPUT_COUNT,
            SNMP_OID_UNITS_OUTLET_COUNT,
        ]
    )

    entities: list[SensorEntity] = []

    for index in range(1, device[SNMP_OID_UNITS_INPUT_COUNT] + 1):
        entities.append(SnmpInputCurrentSensorEntity(api, device, index))
        entities.append(SnmpInputVoltageSensorEntity(api, device, index))
        entities.append(SnmpInputWattsSensorEntity(api, device, index))
        entities.append(SnmpInputWattHoursSensorEntity(api, device, index))

    for index in range(1, device[SNMP_OID_UNITS_OUTLET_COUNT] + 1):
        entities.append(SnmpOutletCurrentSensorEntity(api, device, index))
        # entities.append(SnmpOutletVoltageSensorEntity(api, device, index))
        entities.append(SnmpOutletWattsSensorEntity(api, device, index))
        entities.append(SnmpOutletWattHoursSensorEntity(api, device, index))

    async_add_entities(entities)


class SnmpSensorEntity(SnmpEntity, SensorEntity):
    """Representation of a SNMP ePDU sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    _name_oid: str | None = None
    _value_oid: str | None = None

    _multiplier: float | None = None

    _name_prefix: str = ""
    _name_suffix: str = ""

    def __init__(self, api: SnmpApi, device: dict) -> None:
        """Initialize a SNMP ePDU sensor."""
        super().__init__(api, device)
        data = self._api.get(oids=[self._name_oid, self._value_oid])
        self._attr_name = f"{self._device.get(SNMP_OID_UNITS_PRODUCT_NAME)} {self._name_prefix} {data.get(self._name_oid)} {self._name_suffix}"
        self._attr_unique_id = f"{DOMAIN}_{self._device.get(SNMP_OID_UNITS_SERIAL_NUMBER)}_{self._value_oid}"
        self._attr_native_value = data.get(self._value_oid)
        if self._multiplier is not None:
            self._attr_native_value *= self._multiplier

    async def async_update(self) -> None:
        """Get the latest device data."""
        data = self._api.get(oids=[self._value_oid])
        self._attr_native_value = data.get(self._value_oid)
        if self._multiplier is not None:
            self._attr_native_value *= self._multiplier


class SnmpInputSensorEntity(SnmpSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU input sensor."""

    _name_prefix = "Input"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU input sensor."""
        self._name_oid = SNMP_OID_INPUTS_FEED_NAME.replace("x", str(index))
        super().__init__(api, device)


class SnmpInputCurrentSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU input current sensor."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = ELECTRIC_CURRENT_AMPERE

    _multiplier = 0.001
    _name_suffix = "Current"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU input current sensor."""
        self._value_oid = SNMP_OID_INPUTS_CURRENT.replace("x", str(index))
        super().__init__(api, device, index)


class SnmpInputVoltageSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU input voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = ELECTRIC_POTENTIAL_VOLT

    _multiplier = 0.001
    _name_suffix = "Voltage"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU input voltage sensor."""
        self._value_oid = SNMP_OID_INPUTS_VOLTAGE.replace("x", str(index))
        super().__init__(api, device, index)


class SnmpInputWattsSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU input watts sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = POWER_WATT

    _name_suffix = "Watts"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU input watts sensor."""
        self._value_oid = SNMP_OID_INPUTS_WATTS.replace("x", str(index))
        super().__init__(api, device, index)


class SnmpInputWattHoursSensorEntity(SnmpInputSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU input watt hours sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = ENERGY_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    _name_suffix = "Watt Hours"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU input watt hours sensor."""
        self._value_oid = SNMP_OID_INPUTS_WATT_HOURS.replace("x", str(index))
        super().__init__(api, device, index)


class SnmpOutletSensorEntity(SnmpSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU outlet sensor."""

    _name_prefix = "Outlet"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU outlet sensor."""
        self._name_oid = SNMP_OID_OUTLETS_DESIGNATOR.replace("x", str(index))
        super().__init__(api, device)


class SnmpOutletCurrentSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU outlet current sensor."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = ELECTRIC_CURRENT_AMPERE

    _multiplier = 0.001
    _name_suffix = "Current"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU outlet current sensor."""
        self._value_oid = SNMP_OID_OUTLETS_CURRENT.replace("x", str(index))
        super().__init__(api, device, index)


class SnmpOutletVoltageSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU outlet voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = ELECTRIC_POTENTIAL_VOLT

    _multiplier = 0.001
    _name_suffix = "Voltage"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU outlet voltage sensor."""
        self._value_oid = SNMP_OID_OUTLETS_VOLTAGE.replace("x", str(index))
        super().__init__(api, device, index)


class SnmpOutletWattsSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU outlet watts sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = POWER_WATT

    _name_suffix = "Watts"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU outlet watts sensor."""
        self._value_oid = SNMP_OID_OUTLETS_WATTS.replace("x", str(index))
        super().__init__(api, device, index)


class SnmpOutletWattHoursSensorEntity(SnmpOutletSensorEntity, SensorEntity):
    """Representation of a SNMP ePDU outlet watt hours sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = ENERGY_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    _name_suffix = "Watt Hours"

    def __init__(self, api: SnmpApi, device: dict, index: int) -> None:
        """Initialize a SNMP ePDU outlet watt hours sensor."""
        self._value_oid = SNMP_OID_OUTLETS_WATT_HOURS.replace("x", str(index))
        super().__init__(api, device, index)
