"""Tests for ePDU device identifier fallbacks."""

import pytest

from custom_components.eaton_epdu.const import (
    SNMP_OID_UNITS_DEVICE_NAME,
    SNMP_OID_UNITS_PART_NUMBER,
    SNMP_OID_UNITS_PRODUCT_NAME,
    SNMP_OID_UNITS_SERIAL_NUMBER,
)
from custom_components.eaton_epdu.coordinator import SnmpCoordinator
from custom_components.eaton_epdu.sensor import SnmpInputCurrentSensorEntity

SERIAL = SNMP_OID_UNITS_SERIAL_NUMBER.replace("unit", "1")
DEVICE_NAME = SNMP_OID_UNITS_DEVICE_NAME.replace("unit", "1")
PART_NUMBER = SNMP_OID_UNITS_PART_NUMBER.replace("unit", "1")
PRODUCT_NAME = SNMP_OID_UNITS_PRODUCT_NAME.replace("unit", "1")


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param({SERIAL: "serial", DEVICE_NAME: "name"}, "serial", id="serial"),
        pytest.param({SERIAL: "", DEVICE_NAME: "name"}, "name", id="empty-serial"),
        pytest.param({SERIAL: None, PART_NUMBER: "part"}, "part", id="part"),
        pytest.param({PRODUCT_NAME: "product"}, "product", id="product"),
        pytest.param({}, "192.0.2.1_1", id="host-and-unit"),
    ],
)
async def test_identifier_fallbacks(
    coordinator: SnmpCoordinator, data: dict[str, str | None], expected: str
) -> None:
    """Device identifiers must use nonempty fallback metadata."""
    coordinator.data = data
    sensor = SnmpInputCurrentSensorEntity(coordinator, "1", "1")
    assert sensor.identifier == expected
    assert sensor.device_info["identifiers"] == {("eaton_epdu", expected)}
