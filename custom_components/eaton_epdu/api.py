"""API for Eaton ePDU."""

from __future__ import annotations

import logging

from pysnmp.error import PySnmpError
import pysnmp.hlapi.asyncio as hlapi
from pysnmp.hlapi.asyncio import SnmpEngine
from pysnmp.proto.rfc1902 import Integer, OctetString

from homeassistant.config_entries import ConfigEntry

from .const import (
    ATTR_AUTH_KEY,
    ATTR_AUTH_KEY_WRITE,
    ATTR_AUTH_PROTOCOL,
    ATTR_AUTH_PROTOCOL_WRITE,
    ATTR_COMMUNITY,
    ATTR_COMMUNITY_WRITE,
    ATTR_HOST,
    ATTR_PORT,
    ATTR_PRIV_KEY,
    ATTR_PRIV_KEY_WRITE,
    ATTR_PRIV_PROTOCOL,
    ATTR_PRIV_PROTOCOL_WRITE,
    ATTR_USERNAME,
    ATTR_USERNAME_WRITE,
    ATTR_VERSION,
    ATTR_VERSION_WRITE,
    SNMP_PORT_DEFAULT,
    AuthProtocol,
    PrivProtocol,
    SnmpVersion,
)

AUTH_MAP = {
    AuthProtocol.NO_AUTH: hlapi.USM_AUTH_NONE,
    AuthProtocol.MD5: hlapi.USM_AUTH_HMAC96_MD5,
    AuthProtocol.SHA: hlapi.USM_AUTH_HMAC96_SHA,
    AuthProtocol.SHA_224: hlapi.USM_AUTH_HMAC128_SHA224,
    AuthProtocol.SHA_256: hlapi.USM_AUTH_HMAC192_SHA256,
    AuthProtocol.SHA_384: hlapi.USM_AUTH_HMAC256_SHA384,
    AuthProtocol.SHA_512: hlapi.USM_AUTH_HMAC384_SHA512,
}

PRIV_MAP = {
    PrivProtocol.NO_PRIV: hlapi.USM_PRIV_NONE,
    PrivProtocol.DES: hlapi.USM_PRIV_CBC56_DES,
    PrivProtocol.DES_3: hlapi.USM_PRIV_CBC168_3DES,
    PrivProtocol.AES: hlapi.USM_PRIV_CFB128_AES,
    PrivProtocol.AES_192: hlapi.USM_PRIV_CFB192_AES,
    PrivProtocol.AES_256: hlapi.USM_PRIV_CFB256_AES,
    PrivProtocol.AES_BLUMENTHAL_192: hlapi.USM_PRIV_CFB192_AES_BLUMENTHAL,
    PrivProtocol.AES_BLUMENTHAL_256: hlapi.USM_PRIV_CFB256_AES_BLUMENTHAL,
}

_LOGGER = logging.getLogger(__name__)


class SnmpApi:
    """Provide an api for Eaton ePDU."""

    _credentials: hlapi.CommunityData | hlapi.UsmUserData
    _credentials_write: hlapi.CommunityData | hlapi.UsmUserData | None
    _target: hlapi.UdpTransportTarget | hlapi.Udp6TransportTarget
    _version: str
    _version_write: str | None

    def __init__(self, snmpEngine: SnmpEngine) -> None:
        """Init the SnmpApi."""
        self._snmpEngine = snmpEngine

    async def setup(self, entry: ConfigEntry) -> None:
        """Setup the SnmpApi."""
        try:
            self._target = await hlapi.UdpTransportTarget.create(
                (
                    entry.data.get(ATTR_HOST),
                    entry.data.get(ATTR_PORT, SNMP_PORT_DEFAULT),
                ),
                10,
            )
        except PySnmpError:
            try:
                self._target = await hlapi.Udp6TransportTarget.create(
                    (
                        entry.data.get(ATTR_HOST),
                        entry.data.get(ATTR_PORT, SNMP_PORT_DEFAULT),
                    ),
                    10,
                )
            except PySnmpError as err:
                _LOGGER.error("Invalid SNMP host: %s", err)
                return

        self._version = entry.data.get(ATTR_VERSION)
        if self._version == SnmpVersion.V1:
            self._credentials = hlapi.CommunityData(
                entry.data.get(ATTR_COMMUNITY), mpModel=0
            )
        elif self._version == SnmpVersion.V3:
            self._credentials = hlapi.UsmUserData(
                entry.data.get(ATTR_USERNAME),
                entry.data.get(ATTR_AUTH_KEY),
                entry.data.get(ATTR_PRIV_KEY),
                AUTH_MAP.get(entry.data.get(ATTR_AUTH_PROTOCOL, AuthProtocol.NO_AUTH)),
                PRIV_MAP.get(entry.data.get(ATTR_PRIV_PROTOCOL, PrivProtocol.NO_PRIV)),
            )

        self._version_write = entry.data.get(ATTR_VERSION_WRITE)
        if self._version_write == SnmpVersion.V1:
            self._credentials_write = hlapi.CommunityData(
                entry.data.get(ATTR_COMMUNITY_WRITE), mpModel=0
            )
        elif self._version_write == SnmpVersion.V3:
            self._credentials_write = hlapi.UsmUserData(
                entry.data.get(ATTR_USERNAME_WRITE),
                entry.data.get(ATTR_AUTH_KEY_WRITE),
                entry.data.get(ATTR_PRIV_KEY_WRITE),
                AUTH_MAP.get(
                    entry.data.get(ATTR_AUTH_PROTOCOL_WRITE, AuthProtocol.NO_AUTH)
                ),
                PRIV_MAP.get(
                    entry.data.get(ATTR_PRIV_PROTOCOL_WRITE, PrivProtocol.NO_PRIV)
                ),
            )
        else:
            self._credentials_write = None

    @staticmethod
    def construct_object_types(list_of_oids):
        """Prepare desired objects from list of OIDs."""
        return [hlapi.ObjectType(hlapi.ObjectIdentity(oid)) for oid in list_of_oids]

    async def get(self, oids) -> dict:
        """Get data for given OIDs in a single call."""
        while len(oids):
            _LOGGER.debug("Get OID(s) %s", oids)

            (
                error_indication,
                error_status,
                error_index,
                var_binds,
            ) = await hlapi.get_cmd(
                self._snmpEngine,
                self._credentials,
                self._target,
                hlapi.ContextData(),
                *__class__.construct_object_types(oids),
            )

            if error_index:
                _LOGGER.debug("Remove error index %d", error_index - 1)
                oids.pop(error_index - 1)
                continue

            if error_indication or error_status:
                raise RuntimeError(
                    f"Got SNMP error: {error_indication} {error_status} {error_index}"
                )

            items = {}
            for var_bind in var_binds:
                items[str(var_bind[0])] = __class__.cast(var_bind[1])
            return items

        return {}

    async def set(self, oid: str, value, value_type: str = "OctetString") -> bool:
        """Set SNMP value for the given OID.

        Args:
            oid: OID string to set.
            value: The value to set.
            value_type: Type of the SNMP value as string ("OctetString", "Integer", etc.)

        Returns:
            True if set succeeded, otherwise raises RuntimeError.
        """

        # Map value_type string to pysnmp type instance
        if value_type == "OctetString":
            snmp_value = OctetString(value)
        elif value_type == "Integer":
            snmp_value = Integer(value)
        else:
            raise ValueError(f"Unsupported SNMP type: {value_type}")

        # Use separate write credentials if available
        credentials = self._credentials
        if self._credentials_write is not None:
            credentials = self._credentials_write

        error_indication, error_status, error_index, var_binds = await hlapi.set_cmd(
            self._snmpEngine,
            credentials,
            self._target,
            hlapi.ContextData(),
            hlapi.ObjectType(hlapi.ObjectIdentity(oid), snmp_value),
        )

        if error_indication:
            raise RuntimeError(f"SNMP set error: {error_indication}")
        if error_status:
            raise RuntimeError(
                f"SNMP set error at {error_index} - {error_status.prettyPrint()}"
            )
        return True

    async def get_bulk(
        self,
        oids,
        count,
        start_from=1,
    ) -> list:
        """Get table data for given OIDs with defined rown count."""
        del start_from  # Kept for compatibility with existing callers.
        _LOGGER.debug("Get %s bulk OID(s) %s", count, oids)
        if count <= 0 or not oids:
            return []

        result = []
        width = len(oids)
        remaining = count
        var_binds = __class__.construct_object_types(oids)
        while remaining:
            batch_size = min(4, remaining)
            (
                error_indication,
                error_status,
                error_index,
                var_bind_table,
            ) = await hlapi.bulk_cmd(
                self._snmpEngine,
                self._credentials,
                self._target,
                hlapi.ContextData(),
                0,
                batch_size,
                *var_binds,
            )

            if error_indication or error_status:
                raise RuntimeError(
                    f"Got SNMP error: {error_indication} {error_status} {error_index}"
                )

            rows = [
                var_bind_table[index : index + width]
                for index in range(0, len(var_bind_table), width)
                if len(var_bind_table[index : index + width]) == width
            ]
            if not rows:
                break

            for row in rows:
                items = {}
                for var_bind in row:
                    items[str(var_bind[0])] = __class__.cast(var_bind[1])
                result.append(items)

            var_binds = rows[-1]
            remaining -= len(rows)

        return result[:count]

    async def get_bulk_auto(
        self,
        oids,
        count_oid,
        start_from=1,
    ) -> list:
        """Get table data for given OIDs with determined rown count."""
        return await self.get_bulk(
            oids, await self.get([count_oid])[count_oid], start_from
        )

    @staticmethod
    def cast(value):
        """Cast returned value into correct type."""
        try:
            return int(value)
        except ValueError, TypeError:
            try:
                return float(value)
            except ValueError, TypeError:
                try:
                    return str(value)
                except ValueError, TypeError:
                    pass
        return value
