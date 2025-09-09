"""Support for Eaton ePDU switches."""

from __future__ import annotations

import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SNMP_OID_OUTLETS_DESIGNATOR,
    SNMP_OID_OUTLETS_STATUS,
    SNMP_OID_OUTLETS_SWITCH_OFF,
    SNMP_OID_OUTLETS_SWITCH_ON,
    SNMP_OID_UNITS_OUTLET_COUNT,
)
from .coordinator import SnmpCoordinator
from .entity import SnmpEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switches."""

    coordinator = entry.runtime_data
    switches: list[SwitchEntity] = []

    for unit in coordinator.get_units():
        for index in range(
            1,
            coordinator.data.get(SNMP_OID_UNITS_OUTLET_COUNT.replace("unit", unit), 0)
            + 1,
        ):
            if (
                coordinator.data.get(
                    SNMP_OID_OUTLETS_STATUS.replace("unit", unit).replace(
                        "index", str(index)
                    ),
                    None,
                )
                is not None
            ):
                switches.append(SnmpSwitchEntity(coordinator, unit, str(index)))

    async_add_entities(switches)


class SnmpSwitchEntity(SnmpEntity, SwitchEntity):
    """Representation of a Eaton ePDU outlet as a switch."""

    _name_oid = SNMP_OID_OUTLETS_DESIGNATOR
    _name_prefix = "Outlet"
    _name_suffix = "Switch"

    _value_oid = SNMP_OID_OUTLETS_STATUS

    def __init__(self, coordinator: SnmpCoordinator, unit: str, index: str) -> None:
        """Initialize a Eaton ePDU outlet switch."""
        super().__init__(coordinator, unit)
        self._name_oid = self._name_oid.replace("unit", unit).replace("index", index)
        self._value_oid = self._value_oid.replace("unit", unit).replace("index", index)
        device_name = self.device_info["name"]
        sensor_name = self.coordinator.data.get(self._name_oid)
        self._attr_name = (
            f"{device_name} {self._name_prefix} {sensor_name} {self._name_suffix}"
        )
        self._attr_unique_id = f"{DOMAIN}_{self.identifier}_{self._value_oid}"

        self._oid_on = SNMP_OID_OUTLETS_SWITCH_ON.replace("unit", unit).replace(
            "index", index
        )
        self._oid_off = SNMP_OID_OUTLETS_SWITCH_OFF.replace("unit", unit).replace(
            "index", index
        )

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.get(self._value_oid, False)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data.get(self._value_oid, None) is not None

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.coordinator.set_snmp_value(self._oid_on, 1, "Integer")
        await asyncio.sleep(2)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.coordinator.set_snmp_value(self._oid_off, 1, "Integer")
        await asyncio.sleep(2)
        await self.coordinator.async_refresh()
