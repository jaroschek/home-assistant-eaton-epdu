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
    """Base class for myUplink Entities."""

    @property
    def device_info(self):
        """Return the device_info of the device."""
        model = self.coordinator.data.get(SNMP_OID_UNITS_PRODUCT_NAME)
        name = self.coordinator.data.get(SNMP_OID_UNITS_DEVICE_NAME)
        if name:
            model = f"{self.coordinator.data.get(SNMP_OID_UNITS_PART_NUMBER)} {model}"
        else:
            name = self.coordinator.data.get(SNMP_OID_UNITS_PART_NUMBER)

        return DeviceInfo(
            identifiers={
                (DOMAIN, self.coordinator.data.get(SNMP_OID_UNITS_SERIAL_NUMBER))
            },
            manufacturer=MANUFACTURER,
            model=model,
            name=name,
            sw_version=self.coordinator.data.get(SNMP_OID_UNITS_FIRMWARE_VERSION),
        )
