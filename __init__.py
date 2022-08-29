"""The SNMP ePDU integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import SnmpApi
from .const import SNMP_API_CLIENT, DOMAIN, PLATFORMS


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up myUplink."""
    hass.data[DOMAIN] = {}

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SNMP ePDU from a config entry."""
    hass.data[DOMAIN][entry.entry_id] = {SNMP_API_CLIENT: SnmpApi(entry)}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
