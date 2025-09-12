"""Eaton ePDU coordinator."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SnmpApi
from .const import (
    ATTR_UPDATE_INTERVAL,
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
    SNMP_OID_OUTLETS_STATUS,
    SNMP_OID_OUTLETS_WATT_HOURS,
    SNMP_OID_OUTLETS_WATTS,
    SNMP_OID_UNITS,
    SNMP_OID_UNITS_DEVICE_NAME,
    SNMP_OID_UNITS_FIRMWARE_VERSION,
    SNMP_OID_UNITS_INPUT_COUNT,
    SNMP_OID_UNITS_OUTLET_COUNT,
    SNMP_OID_UNITS_PART_NUMBER,
    SNMP_OID_UNITS_PRODUCT_NAME,
    SNMP_OID_UNITS_SERIAL_NUMBER,
    UPDATE_INTERVAL_DEFAULT,
)

_LOGGER = logging.getLogger(__name__)


class SnmpCoordinator(DataUpdateCoordinator):
    """Data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: SnmpApi) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.data.get(ATTR_UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT)
            ),
        )
        self._api = api

    async def _update_data(self) -> dict:
        """Fetch the latest data from the source."""
        try:
            if self.data is None:
                self.data = await self._api.get([SNMP_OID_UNITS])
            else:
                self.data.update(await self._api.get([SNMP_OID_UNITS]))

            for unit in self.get_units():
                self.data.update(
                    await self._api.get(
                        [
                            SNMP_OID_UNITS_PRODUCT_NAME.replace("unit", unit),
                            SNMP_OID_UNITS_PART_NUMBER.replace("unit", unit),
                            SNMP_OID_UNITS_SERIAL_NUMBER.replace("unit", unit),
                            SNMP_OID_UNITS_FIRMWARE_VERSION.replace("unit", unit),
                            SNMP_OID_UNITS_DEVICE_NAME.replace("unit", unit),
                            SNMP_OID_UNITS_INPUT_COUNT.replace("unit", unit),
                            SNMP_OID_UNITS_OUTLET_COUNT.replace("unit", unit),
                        ]
                    )
                )

                input_count = self.data.get(
                    SNMP_OID_UNITS_INPUT_COUNT.replace("unit", unit), 0
                )
                if input_count > 0:
                    for result in await self._api.get_bulk(
                        [
                            SNMP_OID_INPUTS_FEED_NAME.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_INPUTS_CURRENT.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_INPUTS_PF.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_INPUTS_VOLTAGE.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_INPUTS_WATTS.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_INPUTS_WATT_HOURS.replace("unit", unit).replace(
                                "index", ""
                            ),
                        ],
                        input_count,
                    ):
                        self.data.update(result)

                outlet_count = self.data.get(
                    SNMP_OID_UNITS_OUTLET_COUNT.replace("unit", unit), 0
                )
                if outlet_count > 0:
                    for result in await self._api.get_bulk(
                        [
                            SNMP_OID_OUTLETS_DESIGNATOR.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_OUTLETS_CURRENT.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_OUTLETS_PF.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_OUTLETS_WATTS.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_OUTLETS_WATT_HOURS.replace("unit", unit).replace(
                                "index", ""
                            ),
                            SNMP_OID_OUTLETS_STATUS.replace("unit", unit).replace(
                                "index", ""
                            ),
                        ],
                        outlet_count,
                    ):
                        self.data.update(result)

            return self.data

        except RuntimeError as err:
            raise UpdateFailed(err) from err

    def get_units(self) -> dict:
        """Get units as dict."""
        units = self.data.get(SNMP_OID_UNITS)

        if units is None:
            return []

        if isinstance(units, str) and units.find(",") != -1:
            units = units.split(",")
        else:
            units = [str(units)]

        return units

    async def _async_update_data(self) -> dict:
        """Fetch the latest data from the source."""
        return await self._update_data()

    async def set_snmp_value(
        self, oid: str, value, value_type: str = "OctetString"
    ) -> bool:
        """Set SNMP value and refresh data."""
        try:
            result = await self._api.set(oid, value, value_type)
            _LOGGER.debug("Successfully set SNMP OID %s to %s", oid, value)
            await self.async_refresh()
            return result
        except Exception:
            _LOGGER.error("Failed to set SNMP OID %s: %s", oid, value)
            raise
