"""Config flow for Eaton ePDU integration."""

from __future__ import annotations

import voluptuous as vol
from voluptuous.schema_builder import Schema

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_ACCURATE_POWER,
    ATTR_AUTH_KEY,
    ATTR_AUTH_KEY_WRITE,
    ATTR_AUTH_PROTOCOL,
    ATTR_AUTH_PROTOCOL_WRITE,
    ATTR_COMMUNITY,
    ATTR_COMMUNITY_WRITE,
    ATTR_HOST,
    ATTR_NAME,
    ATTR_PORT,
    ATTR_PRIV_KEY,
    ATTR_PRIV_KEY_WRITE,
    ATTR_PRIV_PROTOCOL,
    ATTR_PRIV_PROTOCOL_WRITE,
    ATTR_UPDATE_INTERVAL,
    ATTR_USERNAME,
    ATTR_USERNAME_WRITE,
    ATTR_VERSION,
    ATTR_VERSION_WRITE,
    DOMAIN,
    SNMP_PORT_DEFAULT,
    UPDATE_INTERVAL_DEFAULT,
    AuthProtocol,
    PrivProtocol,
    SnmpVersion,
    SnmpVersionWrite,
)


def get_host_schema_config(data: ConfigType) -> Schema:
    """Return the host schema for config flow."""
    return vol.Schema(
        {
            vol.Required(ATTR_NAME, default=data.get(ATTR_NAME)): cv.string,
            vol.Required(ATTR_HOST, default=data.get(ATTR_HOST)): cv.string,
            vol.Required(
                ATTR_PORT, default=data.get(ATTR_PORT, SNMP_PORT_DEFAULT)
            ): cv.port,
            vol.Required(
                ATTR_UPDATE_INTERVAL,
                default=data.get(ATTR_UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT),
            ): cv.positive_int,
            vol.Required(
                ATTR_ACCURATE_POWER, default=data.get(ATTR_ACCURATE_POWER, False)
            ): bool,
            vol.Required(
                ATTR_VERSION, default=data.get(ATTR_VERSION) or SnmpVersion.V1
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in SnmpVersion],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                ATTR_VERSION_WRITE,
                default=data.get(ATTR_VERSION_WRITE) or SnmpVersionWrite.NO_Version,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in SnmpVersionWrite],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def get_host_schema_options(data: ConfigType) -> Schema:
    """Return the host schema for options flow."""
    return vol.Schema(
        {
            vol.Required(ATTR_HOST, default=data.get(ATTR_HOST)): cv.string,
            vol.Required(
                ATTR_PORT, default=data.get(ATTR_PORT, SNMP_PORT_DEFAULT)
            ): cv.port,
            vol.Required(
                ATTR_UPDATE_INTERVAL,
                default=data.get(ATTR_UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT),
            ): cv.positive_int,
            vol.Required(
                ATTR_ACCURATE_POWER, default=data.get(ATTR_ACCURATE_POWER, False)
            ): bool,
            vol.Required(
                ATTR_VERSION, default=data.get(ATTR_VERSION) or SnmpVersion.V1
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in SnmpVersion],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                ATTR_VERSION_WRITE,
                default=data.get(ATTR_VERSION_WRITE) or SnmpVersionWrite.NO_Version,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in SnmpVersionWrite],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def get_v1_schema(data: ConfigType) -> Schema:
    """Return the v1 schema."""
    return vol.Schema(
        {
            vol.Required(ATTR_COMMUNITY, default=data.get(ATTR_COMMUNITY)): cv.string,
        }
    )


def get_v1_schema_write(data: ConfigType) -> Schema:
    """Return the v1 schema."""
    return vol.Schema(
        {
            vol.Required(
                ATTR_COMMUNITY_WRITE, default=data.get(ATTR_COMMUNITY_WRITE)
            ): cv.string,
        }
    )


def get_v3_schema(data: ConfigType) -> Schema:
    """Return the v3 schema."""
    return vol.Schema(
        {
            vol.Required(ATTR_USERNAME, default=data.get(ATTR_USERNAME)): cv.string,
            vol.Required(
                ATTR_AUTH_PROTOCOL,
                default=data.get(ATTR_AUTH_PROTOCOL) or AuthProtocol.NO_AUTH,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in AuthProtocol],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(ATTR_AUTH_KEY): cv.string,
            vol.Required(
                ATTR_PRIV_PROTOCOL,
                default=data.get(ATTR_PRIV_PROTOCOL) or PrivProtocol.NO_PRIV,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in PrivProtocol],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(ATTR_PRIV_KEY): cv.string,
        }
    )


def get_v3_schema_write(data: ConfigType) -> Schema:
    """Return the v3 schema."""
    return vol.Schema(
        {
            vol.Required(
                ATTR_USERNAME_WRITE, default=data.get(ATTR_USERNAME_WRITE)
            ): cv.string,
            vol.Required(
                ATTR_AUTH_PROTOCOL_WRITE,
                default=data.get(ATTR_AUTH_PROTOCOL_WRITE) or AuthProtocol.NO_AUTH,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in AuthProtocol],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(ATTR_AUTH_KEY_WRITE): cv.string,
            vol.Required(
                ATTR_PRIV_PROTOCOL_WRITE,
                default=data.get(ATTR_PRIV_PROTOCOL) or PrivProtocol.NO_PRIV,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in PrivProtocol],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(ATTR_PRIV_KEY_WRITE): cv.string,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eaton ePDU."""

    VERSION = 1

    def __init__(self) -> None:
        """Init the ConfigFlow."""
        self.data: ConfigType = {}

    async def async_step_user(self, user_input: ConfigType | None = None) -> FlowResult:
        """Handle the initial step."""
        return await self.async_step_host(host_input=user_input)

    async def async_step_host(self, host_input: ConfigType | None = None) -> FlowResult:
        """Handle the host step."""
        if host_input is not None:
            self.data = host_input

            if host_input[ATTR_VERSION] == SnmpVersion.V1:
                return await self.async_step_v1()

            if host_input[ATTR_VERSION] == SnmpVersion.V3:
                return await self.async_step_v3()

        return self.async_show_form(
            step_id="host", data_schema=get_host_schema_config(data=self.data)
        )

    async def async_step_v1(self, v1_input: ConfigType | None = None) -> FlowResult:
        """Handle the v1 step."""
        if v1_input is None:
            return self.async_show_form(
                step_id="v1", data_schema=get_v1_schema(self.data)
            )

        self.data.update(v1_input)

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V1:
            return await self.async_step_v1_write()

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V3:
            return await self.async_step_v3_write()

        return self.async_create_entry(title=self.data[ATTR_NAME], data=self.data)

    async def async_step_v1_write(
        self, v1_input: ConfigType | None = None
    ) -> FlowResult:
        """Handle the v1 write step."""
        if v1_input is None:
            return self.async_show_form(
                step_id="v1_write", data_schema=get_v1_schema_write(self.data)
            )

        self.data.update(v1_input)

        return self.async_create_entry(title=self.data[ATTR_NAME], data=self.data)

    async def async_step_v3(self, v3_input: ConfigType | None = None) -> FlowResult:
        """Handle the v3 step."""
        if v3_input is None:
            return self.async_show_form(
                step_id="v3", data_schema=get_v3_schema(self.data)
            )

        self.data.update(v3_input)

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V1:
            return await self.async_step_v1_write()

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V3:
            return await self.async_step_v3_write()

        return self.async_create_entry(title=self.data[ATTR_NAME], data=self.data)

    async def async_step_v3_write(
        self, v3_input: ConfigType | None = None
    ) -> FlowResult:
        """Handle the v3 write step."""
        if v3_input is None:
            return self.async_show_form(
                step_id="v3_write", data_schema=get_v3_schema_write(self.data)
            )

        self.data.update(v3_input)

        return self.async_create_entry(title=self.data[ATTR_NAME], data=self.data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Options callback for Eaton ePDU."""
        return OptionsFlow(config_entry)


class OptionsFlow(OptionsFlowWithReload):
    """Handle a options flow for Eaton ePDU."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize Eaton ePDU options flow."""
        self.data = dict(entry.data)

    async def async_step_init(self, user_input: ConfigType | None = None) -> FlowResult:
        """Manage the options."""
        return await self.async_step_host(host_input=user_input)

    async def async_step_host(self, host_input: ConfigType | None = None) -> FlowResult:
        """Handle the host step."""
        if host_input is not None:
            self.data.update(host_input)

            if host_input[ATTR_VERSION_WRITE] == "None":
                self.data.pop(ATTR_VERSION_WRITE, None)
                self.data.pop(ATTR_COMMUNITY_WRITE, None)
                self.data.pop(ATTR_USERNAME_WRITE, None)
                self.data.pop(ATTR_AUTH_KEY_WRITE, None)
                self.data.pop(ATTR_AUTH_PROTOCOL_WRITE, None)
                self.data.pop(ATTR_PRIV_KEY_WRITE, None)
                self.data.pop(ATTR_PRIV_PROTOCOL_WRITE, None)

            if host_input[ATTR_VERSION] == SnmpVersion.V1:
                return await self.async_step_v1()

            if host_input[ATTR_VERSION] == SnmpVersion.V3:
                return await self.async_step_v3()

        return self.async_show_form(
            step_id="host", data_schema=get_host_schema_options(data=self.data)
        )

    async def async_step_v1(self, v1_input: ConfigType | None = None) -> FlowResult:
        """Handle the v1 step."""
        if v1_input is None:
            return self.async_show_form(
                step_id="v1", data_schema=get_v1_schema(self.data)
            )

        self.data.update(v1_input)

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V1:
            return await self.async_step_v1_write()

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V3:
            return await self.async_step_v3_write()

        self.hass.config_entries.async_update_entry(self.config_entry, data=self.data)

        return self.async_create_entry(title="", data={})

    async def async_step_v1_write(
        self, v1_input: ConfigType | None = None
    ) -> FlowResult:
        """Handle the v1 write step."""
        if v1_input is None:
            return self.async_show_form(
                step_id="v1_write", data_schema=get_v1_schema_write(self.data)
            )

        self.data.update(v1_input)

        self.hass.config_entries.async_update_entry(self.config_entry, data=self.data)

        return self.async_create_entry(title="", data={})

    async def async_step_v3(self, v3_input: ConfigType | None = None) -> FlowResult:
        """Handle the v3 step."""
        if v3_input is None:
            return self.async_show_form(
                step_id="v3", data_schema=get_v3_schema(self.data)
            )

        self.data.update(v3_input)

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V1:
            return await self.async_step_v1_write()

        if self.data.get(ATTR_VERSION_WRITE) == SnmpVersion.V3:
            return await self.async_step_v3_write()

        self.hass.config_entries.async_update_entry(self.config_entry, data=self.data)

        return self.async_create_entry(title="", data={})

    async def async_step_v3_write(
        self, v3_input: ConfigType | None = None
    ) -> FlowResult:
        """Handle the v3 write step."""
        if v3_input is None:
            return self.async_show_form(
                step_id="v3_write", data_schema=get_v3_schema_write(self.data)
            )

        self.data.update(v3_input)

        self.hass.config_entries.async_update_entry(self.config_entry, data=self.data)

        return self.async_create_entry(title="", data={})


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
