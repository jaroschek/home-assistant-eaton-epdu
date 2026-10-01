"""Tests for ePDU outlet availability and pending states."""

import pytest

from custom_components.eaton_epdu.const import SNMP_OID_OUTLETS_STATUS
from custom_components.eaton_epdu.coordinator import SnmpCoordinator
from custom_components.eaton_epdu.switch import SnmpSwitchEntity


@pytest.mark.parametrize(
    ("value", "last_update_success", "available", "is_on"),
    [
        pytest.param(0, True, True, False, id="off"),
        pytest.param(1, True, True, True, id="on"),
        pytest.param(2, True, True, False, id="pending-off"),
        pytest.param(3, True, True, True, id="pending-on"),
        pytest.param(1, False, False, True, id="failed-refresh"),
        pytest.param(None, True, False, False, id="missing-status"),
    ],
)
async def test_switch_availability(
    coordinator: SnmpCoordinator,
    value: int | None,
    last_update_success: bool,
    available: bool,
    is_on: bool,
) -> None:
    """Outlet switches must respect failures without changing pending states."""
    coordinator.data[
        SNMP_OID_OUTLETS_STATUS.replace("unit", "1").replace("index", "1")
    ] = value
    coordinator.last_update_success = last_update_success
    switch = SnmpSwitchEntity(coordinator, "1", "1")
    assert switch.available is available
    assert switch.is_on is is_on
