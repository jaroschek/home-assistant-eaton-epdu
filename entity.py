"""Definition of base Eaton ePDU Entity"""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SNMP_OID_UNITS_FIRMWARE_VERSION,
    SNMP_OID_UNITS_PART_NUMBER,
    SNMP_OID_UNITS_PRODUCT_NAME,
    SNMP_OID_UNITS_SERIAL_NUMBER,
)
from .coordinator import SnmpCoordinator


class SnmpEntity(CoordinatorEntity[SnmpCoordinator]):
    """Base class for myUplink Entities."""

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.coordinator.data.get(SNMP_OID_UNITS_SERIAL_NUMBER))
            },
            manufacturer="Eaton",
            model=self.coordinator.data.get(SNMP_OID_UNITS_PRODUCT_NAME),
            name=self.coordinator.data.get(SNMP_OID_UNITS_PART_NUMBER),
            sw_version=self.coordinator.data.get(SNMP_OID_UNITS_FIRMWARE_VERSION),
        )
