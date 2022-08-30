"""Definition of base Eaton ePDU Entity"""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity

from .api import SnmpApi
from .const import (
    DOMAIN,
    SNMP_OID_UNITS_FIRMWARE_VERSION,
    SNMP_OID_UNITS_PART_NUMBER,
    SNMP_OID_UNITS_PRODUCT_NAME,
    SNMP_OID_UNITS_SERIAL_NUMBER,
)


class SnmpEntity(Entity):
    """Base class for myUplink Entities."""

    def __init__(self, api: SnmpApi, device: dict) -> None:
        """Initialize class."""
        self._api = api
        self._device = device

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.get(SNMP_OID_UNITS_SERIAL_NUMBER))},
            manufacturer="Eaton",
            model=self._device.get(SNMP_OID_UNITS_PART_NUMBER),
            name=self._device.get(SNMP_OID_UNITS_PRODUCT_NAME),
            sw_version=self._device.get(SNMP_OID_UNITS_FIRMWARE_VERSION),
        )
