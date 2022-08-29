"""Config flow for SNMP ePDU integration."""
from __future__ import annotations

import voluptuous as vol
from voluptuous.schema_builder import Schema

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
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
    DOMAIN,
    ATTR_NAME,
    ATTR_HOST,
    ATTR_PORT,
    ATTR_VERSION,
    ATTR_COMMUNITY,
    ATTR_USERNAME,
    ATTR_AUTH_KEY,
    ATTR_AUTH_PROTOCOL,
    ATTR_PRIV_KEY,
    ATTR_PRIV_PROTOCOL,
    SNMP_PORT_DEFAULT,
    AuthProtocol,
    PrivProtocol,
    SnmpVersion,
)


def get_host_schema_config(data: ConfigType) -> Schema:
    """Return the host schema for config flow"""
    return vol.Schema(
        {
            vol.Required(ATTR_NAME, default=data.get(ATTR_NAME)): cv.string,
            vol.Required(ATTR_HOST, default=data.get(ATTR_HOST)): cv.string,
            vol.Required(
                ATTR_PORT, default=data.get(ATTR_PORT, SNMP_PORT_DEFAULT)
            ): cv.port,
            vol.Required(
                ATTR_VERSION, default=data.get(ATTR_VERSION) or SnmpVersion.V1
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in SnmpVersion],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def get_host_schema_options(data: ConfigType) -> Schema:
    """Return the host schema for options flow"""
    return vol.Schema(
        {
            vol.Required(ATTR_HOST, default=data.get(ATTR_HOST)): cv.string,
            vol.Required(
                ATTR_PORT, default=data.get(ATTR_PORT, SNMP_PORT_DEFAULT)
            ): cv.port,
            vol.Required(
                ATTR_VERSION, default=data.get(ATTR_VERSION) or SnmpVersion.V1
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in SnmpVersion],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def get_v1_schema(data: ConfigType) -> Schema:
    """Return the v1 schema"""
    return vol.Schema(
        {
            vol.Required(ATTR_COMMUNITY, default=data.get(ATTR_COMMUNITY)): cv.string,
        }
    )


def get_v3_schema(data: ConfigType) -> Schema:
    """Return the v3 schema"""
    return vol.Schema(
        {
            vol.Required(ATTR_USERNAME, default=data.get(ATTR_USERNAME)): cv.string,
            vol.Optional(ATTR_AUTH_KEY): cv.string,
            vol.Required(
                ATTR_AUTH_PROTOCOL,
                default=data.get(ATTR_AUTH_PROTOCOL) or AuthProtocol.NO_AUTH,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in AuthProtocol],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(ATTR_PRIV_KEY): cv.string,
            vol.Required(
                ATTR_PRIV_PROTOCOL,
                default=data.get(ATTR_PRIV_PROTOCOL) or PrivProtocol.NO_PRIV,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[e.value for e in PrivProtocol],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SNMP ePDU."""

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

        _update_v1_input(data=self.data, v1_input=v1_input)

        return self.async_create_entry(title=self.data[ATTR_NAME], data=self.data)

    async def async_step_v3(self, v3_input: ConfigType | None = None) -> FlowResult:
        """Handle the v3 step."""
        if v3_input is None:
            return self.async_show_form(
                step_id="v3", data_schema=get_v3_schema(self.data)
            )

        _update_v3_input(data=self.data, v3_input=v3_input)

        return self.async_create_entry(title=self.data[ATTR_NAME], data=self.data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Options callback for SNMP ePDU."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle a options flow for SNMP ePDU."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize SNMP ePDU options flow."""
        self.config_entry = entry
        self.options = dict(entry.options)

    async def async_step_init(self, user_input: ConfigType | None = None) -> FlowResult:
        """Manage the options."""
        return await self.async_step_host(host_input=user_input)

    async def async_step_host(self, host_input: ConfigType | None = None) -> FlowResult:
        """Handle the host step."""
        if host_input is not None:
            self.options.update(host_input)

            if host_input[ATTR_VERSION] == SnmpVersion.V1:
                return await self.async_step_v1()

            if host_input[ATTR_VERSION] == SnmpVersion.V3:
                return await self.async_step_v3()

        return self.async_show_form(
            step_id="host", data_schema=get_host_schema_options(data=self.options)
        )

    async def async_step_v1(self, v1_input: ConfigType | None = None) -> FlowResult:
        """Handle the v1 step."""
        if v1_input is None:
            return self.async_show_form(
                step_id="v1", data_schema=get_v1_schema(self.options)
            )

        self.options.update(v1_input)

        return self.async_create_entry(title="", data=self.options)

    async def async_step_v3(self, v3_input: ConfigType | None = None) -> FlowResult:
        """Handle the v3 step."""
        if v3_input is None:
            return self.async_show_form(
                step_id="v3", data_schema=get_v3_schema(self.options)
            )

        self.options.update(v3_input)

        return self.async_create_entry(title="", data=self.options)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


def _update_v1_input(data: ConfigType, v1_input: ConfigType) -> None:
    if v1_input is not None:
        data[ATTR_COMMUNITY] = v1_input[ATTR_COMMUNITY]


def _update_v3_input(data: ConfigType, v3_input: ConfigType) -> None:
    if v3_input is not None:
        data[ATTR_USERNAME] = v3_input[ATTR_USERNAME]
        if ATTR_AUTH_KEY in v3_input:
            data[ATTR_AUTH_KEY] = v3_input[ATTR_AUTH_KEY]
        data[ATTR_AUTH_PROTOCOL] = v3_input[ATTR_AUTH_PROTOCOL]
        if ATTR_PRIV_KEY in v3_input:
            data[ATTR_PRIV_KEY] = v3_input[ATTR_PRIV_KEY] or None
        data[ATTR_PRIV_PROTOCOL] = v3_input[ATTR_PRIV_PROTOCOL]
