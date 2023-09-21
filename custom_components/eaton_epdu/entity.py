"""Definition of base Eaton ePDU Entity"""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    SNMP_OID_UNITS_DEVICE_NAME,
    SNMP_OID_UNITS_FIRMWARE_VERSION,
    SNMP_OID_UNITS_PART_NUMBER,
    SNMP_OID_UNITS_PRODUCT_NAME,
    SNMP_OID_UNITS_SERIAL_NUMBER,
)
from .coordinator import SnmpCoordinator


class SnmpEntity(CoordinatorEntity[SnmpCoordinator]):
    """Base class for Eaton ePDU entities."""

    def __init__(self, coordinator: SnmpCoordinator, unit: str) -> None:
        """Initialize a Eaton ePDU entity."""
        super().__init__(coordinator)
        self._unit = unit

    def get_unit_data(self, oid: str, default=None):
        """Wrapper to fetch data from coordinator for current unit"""
        return self.coordinator.data.get(oid.replace("unit", self._unit), default)

    @property
    def device_info(self):
        """Return the device_info of the device."""
        model = self.get_unit_data(SNMP_OID_UNITS_PRODUCT_NAME)
        name = self.get_unit_data(SNMP_OID_UNITS_DEVICE_NAME)
        if name:
            model = f"{self.get_unit_data(SNMP_OID_UNITS_PART_NUMBER)} {model}"
        else:
            name = self.get_unit_data(SNMP_OID_UNITS_PART_NUMBER)

        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.get_unit_data(SNMP_OID_UNITS_SERIAL_NUMBER),
                )
            },
            manufacturer=MANUFACTURER,
            model=model,
            name=name,
            sw_version=self.get_unit_data(SNMP_OID_UNITS_FIRMWARE_VERSION),
        )
