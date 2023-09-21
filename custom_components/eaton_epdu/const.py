"""Constants for the Eaton ePDU integration."""
from __future__ import annotations

from enum import StrEnum

from homeassistant.const import Platform

DOMAIN = "eaton_epdu"

MANUFACTURER = "Eaton"

PLATFORMS = [
    Platform.SENSOR,
]

ATTR_NAME = "name"
ATTR_HOST = "host"
ATTR_PORT = "port"
ATTR_VERSION = "version"
ATTR_COMMUNITY = "community"
ATTR_USERNAME = "username"
ATTR_AUTH_PROTOCOL = "auth_protocol"
ATTR_AUTH_KEY = "auth_key"
ATTR_PRIV_PROTOCOL = "priv_protocol"
ATTR_PRIV_KEY = "priv_key"


class SnmpVersion(StrEnum):
    """Enum with snmp versions."""

    V1 = "1"
    V3 = "3"


class AuthProtocol(StrEnum):
    """Enum with snmp auth protocol options."""

    NO_AUTH = "no auth"
    MD5 = "md5"
    SHA = "sha"
    SHA_224 = "sha224"
    SHA_256 = "sha256"
    SHA_384 = "sha384"
    SHA_512 = "sha512"


class PrivProtocol(StrEnum):
    """Enum with snmp priv protocol options."""

    NO_PRIV = "no priv"
    DES = "des"
    DES_3 = "des3"
    AES = "aes"
    AES_192 = "aes192"
    AES_256 = "aes256"
    AES_BLUMENTHAL_192 = "aesBlumenthal192"
    AES_BLUMENTHAL_256 = "aesBlumenthal256"


SNMP_API_CLIENT = "snmp_api_client"

SNMP_PORT_DEFAULT = 161

SNMP_OID_UNITS = "1.3.6.1.4.1.534.6.6.7.1.1.0"
SNMP_OID_UNITS_PRODUCT_NAME = "1.3.6.1.4.1.534.6.6.7.1.2.1.2.unit"
SNMP_OID_UNITS_PART_NUMBER = "1.3.6.1.4.1.534.6.6.7.1.2.1.3.unit"
SNMP_OID_UNITS_SERIAL_NUMBER = "1.3.6.1.4.1.534.6.6.7.1.2.1.4.unit"
SNMP_OID_UNITS_FIRMWARE_VERSION = "1.3.6.1.4.1.534.6.6.7.1.2.1.5.unit"
SNMP_OID_UNITS_DEVICE_NAME = "1.3.6.1.4.1.534.6.6.7.1.2.1.6.unit"
SNMP_OID_UNITS_INPUT_COUNT = "1.3.6.1.4.1.534.6.6.7.1.2.1.20.unit"
SNMP_OID_UNITS_OUTLET_COUNT = "1.3.6.1.4.1.534.6.6.7.1.2.1.22.unit"

SNMP_OID_INPUTS_FEED_NAME = "1.3.6.1.4.1.534.6.6.7.3.1.1.10.unit.index"
SNMP_OID_INPUTS_VOLTAGE = "1.3.6.1.4.1.534.6.6.7.3.2.1.3.unit.1.index"
SNMP_OID_INPUTS_CURRENT = "1.3.6.1.4.1.534.6.6.7.3.3.1.4.unit.1.index"
SNMP_OID_INPUTS_WATTS = "1.3.6.1.4.1.534.6.6.7.3.4.1.4.unit.1.index"
SNMP_OID_INPUTS_WATT_HOURS = "1.3.6.1.4.1.534.6.6.7.3.4.1.5.unit.1.index"

SNMP_OID_OUTLETS_ID = "1.3.6.1.4.1.534.6.6.7.6.1.1.2.unit.index"
SNMP_OID_OUTLETS_NAME = "1.3.6.1.4.1.534.6.6.7.6.1.1.3.unit.index"
SNMP_OID_OUTLETS_DESIGNATOR = "1.3.6.1.4.1.534.6.6.7.6.1.1.6.unit.index"
SNMP_OID_OUTLETS_CURRENT = "1.3.6.1.4.1.534.6.6.7.6.4.1.3.unit.index"
SNMP_OID_OUTLETS_WATTS = "1.3.6.1.4.1.534.6.6.7.6.5.1.3.unit.index"
SNMP_OID_OUTLETS_WATT_HOURS = "1.3.6.1.4.1.534.6.6.7.6.5.1.4.unit.index"
