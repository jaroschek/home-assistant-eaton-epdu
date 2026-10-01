"""Support for Eaton ePDU switches."""

from __future__ import annotations

import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
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

    _name_suffix = "Switch"

    _value_oid = SNMP_OID_OUTLETS_STATUS

    def __init__(self, coordinator: SnmpCoordinator, unit: str, index: str) -> None:
        """Initialize a Eaton ePDU outlet switch."""
        super().__init__(coordinator, unit)
        self._value_oid = self._value_oid.replace("unit", unit).replace("index", index)
        device_name = self.device_info["name"]
        outlet_label = self.get_outlet_label(index)
        self._attr_name = f"{device_name} {outlet_label} {self._name_suffix}"
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
        # Eaton reports 0=off, 1=on, 2=pendingOff and 3=pendingOn.
        # Treat the pending states as their requested target so Home Assistant
        # reflects a switch command without waiting for the next polling cycle.
        return self.coordinator.data.get(self._value_oid) in (1, 3)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available and self.coordinator.data.get(self._value_oid) is not None
        )

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
