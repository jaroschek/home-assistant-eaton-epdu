"""API for Eaton ePDU."""
from __future__ import annotations

from pysnmp import hlapi

from homeassistant.config_entries import ConfigEntry

from .const import (
    ATTR_AUTH_KEY,
    ATTR_AUTH_PROTOCOL,
    ATTR_COMMUNITY,
    ATTR_HOST,
    ATTR_PORT,
    ATTR_PRIV_KEY,
    ATTR_PRIV_PROTOCOL,
    ATTR_USERNAME,
    ATTR_VERSION,
    SNMP_PORT_DEFAULT,
    AuthProtocol,
    PrivProtocol,
    SnmpVersion,
)

AUTH_MAP = {
    AuthProtocol.NO_AUTH: hlapi.usmNoAuthProtocol,
    AuthProtocol.MD5: hlapi.usmHMACMD5AuthProtocol,
    AuthProtocol.SHA: hlapi.usmHMACSHAAuthProtocol,
    AuthProtocol.SHA_224: hlapi.usmHMAC128SHA224AuthProtocol,
    AuthProtocol.SHA_256: hlapi.usmHMAC192SHA256AuthProtocol,
    AuthProtocol.SHA_384: hlapi.usmHMAC256SHA384AuthProtocol,
    AuthProtocol.SHA_512: hlapi.usmHMAC384SHA512AuthProtocol,
}

PRIV_MAP = {
    PrivProtocol.NO_PRIV: hlapi.usmNoPrivProtocol,
    PrivProtocol.DES: hlapi.usmDESPrivProtocol,
    PrivProtocol.DES_3: hlapi.usm3DESEDEPrivProtocol,
    PrivProtocol.AES: hlapi.usmAesCfb128Protocol,
    PrivProtocol.AES_192: hlapi.usmAesCfb192Protocol,
    PrivProtocol.AES_256: hlapi.usmAesCfb256Protocol,
    PrivProtocol.AES_BLUMENTHAL_192: hlapi.usmAesBlumenthalCfb192Protocol,
    PrivProtocol.AES_BLUMENTHAL_256: hlapi.usmAesBlumenthalCfb256Protocol,
}


class SnmpApi:
    """Provide an api for Eaton ePDU."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Init the SnmpApi."""
        self._target = hlapi.UdpTransportTarget(
            (
                entry.data.get(ATTR_HOST),
                entry.data.get(ATTR_PORT, SNMP_PORT_DEFAULT),
            ),
            10,
        )

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

    @staticmethod
    def construct_object_types(list_of_oids):
        """Prepare desired objects from list of OIDs."""
        object_types = []
        for oid in list_of_oids:
            object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
        return object_types

    def get(self, oids) -> list:
        """Get data for given OIDs in a single call."""
        iterator = hlapi.getCmd(
            hlapi.SnmpEngine(),
            self._credentials,
            self._target,
            hlapi.ContextData(),
            *__class__.construct_object_types(oids),
        )
        return __class__.fetch(iterator, 1)[0]

    def get_bulk(
        self,
        oids,
        count,
        start_from=1,
    ) -> list:
        """Get table data for given OIDs with defined rown count."""
        iterator = hlapi.bulkCmd(
            hlapi.SnmpEngine(),
            self._credentials,
            self._target,
            hlapi.ContextData(),
            start_from,
            count,
            *__class__.construct_object_types(oids),
        )
        return __class__.fetch(iterator, count)

    def get_bulk_auto(
        self,
        oids,
        count_oid,
        start_from=1,
    ):
        """Get table data for given OIDs with determined rown count."""
        return self.get_bulk(oids, self.get([count_oid])[count_oid], start_from)

    @staticmethod
    def cast(value):
        """Cast returned value into correct type."""
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return float(value)
            except (ValueError, TypeError):
                try:
                    return str(value)
                except (ValueError, TypeError):
                    pass
        return value

    @staticmethod
    def fetch(iterator, count) -> list:
        """Fetch data from iterator."""
        result = []
        for _i in range(count):
            try:
                error_indication, error_status, error_index, var_binds = next(iterator)
                if not error_indication and not error_status:
                    items = {}
                    for var_bind in var_binds:
                        items[str(var_bind[0])] = __class__.cast(var_bind[1])
                    result.append(items)
                else:
                    raise RuntimeError(
                        "Got SNMP error: {} {} {}".format(
                            error_indication, error_status, error_index
                        )
                    )
            except StopIteration:
                break
        return result
