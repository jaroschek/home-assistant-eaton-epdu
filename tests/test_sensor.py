"""Tests for missing and calculated ePDU measurements."""

from unittest.mock import patch

import pytest

from custom_components.eaton_epdu.const import (
    SNMP_OID_INPUTS_CURRENT,
    SNMP_OID_INPUTS_PF,
    SNMP_OID_INPUTS_VOLTAGE,
    SNMP_OID_OUTLETS_CURRENT,
    SNMP_OID_OUTLETS_PF,
)
from custom_components.eaton_epdu.coordinator import SnmpCoordinator
from custom_components.eaton_epdu.sensor import (
    SnmpInputCurrentSensorEntity,
    SnmpInputVAPhiSensorEntity,
    SnmpOutputVAPhiSensorEntity,
)

READING = SNMP_OID_INPUTS_CURRENT.replace("unit", "1").replace("index", "1")


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param({}, None, id="missing"),
        pytest.param({READING: None}, None, id="none"),
        pytest.param({READING: ""}, None, id="empty"),
        pytest.param({READING: 0}, 0, id="zero"),
        pytest.param({READING: 1234}, 1.234, id="measurement"),
    ],
)
async def test_sensor_readings(
    coordinator: SnmpCoordinator,
    data: dict[str, int | str | None],
    expected: float | None,
) -> None:
    """Unknown measurements must not become zeros or cause arithmetic errors."""
    coordinator.data.update(data)
    sensor = SnmpInputCurrentSensorEntity(coordinator, "1", "1")
    assert sensor.native_value == expected


async def test_sensor_update_missing(coordinator: SnmpCoordinator) -> None:
    """An existing sensor must become unknown when its reading disappears."""
    coordinator.data[READING] = 1234
    sensor = SnmpInputCurrentSensorEntity(coordinator, "1", "1")
    coordinator.data.pop(READING)
    with patch(
        "homeassistant.helpers.entity.Entity.async_write_ha_state"
    ) as write_state:
        sensor._handle_coordinator_update()
        write_state.assert_called_once()
    assert sensor.native_value is None


@pytest.mark.parametrize(
    ("entity_type", "indices", "current_oid", "pf_oid"),
    [
        pytest.param(
            SnmpInputVAPhiSensorEntity,
            ("1", "1"),
            SNMP_OID_INPUTS_CURRENT,
            SNMP_OID_INPUTS_PF,
            id="input",
        ),
        pytest.param(
            SnmpOutputVAPhiSensorEntity,
            ("1", "1", "1"),
            SNMP_OID_OUTLETS_CURRENT,
            SNMP_OID_OUTLETS_PF,
            id="outlet",
        ),
    ],
)
@pytest.mark.parametrize(
    ("values", "expected"),
    [
        pytest.param((230000, 1000, -1000), 230, id="power"),
        pytest.param((230000, 0, 1000), 0, id="zero-current"),
        pytest.param((None, 1000, 1000), None, id="missing-voltage"),
        pytest.param((230000, None, 1000), None, id="missing-current"),
        pytest.param((230000, 1000, None), None, id="missing-power-factor"),
        pytest.param((230000, "", 1000), None, id="empty-current"),
    ],
)
async def test_calculated_power(
    coordinator: SnmpCoordinator,
    entity_type: type[SnmpInputVAPhiSensorEntity | SnmpOutputVAPhiSensorEntity],
    indices: tuple[str, ...],
    current_oid: str,
    pf_oid: str,
    values: tuple[int | str | None, ...],
    expected: float | None,
) -> None:
    """Calculated power must require every input while retaining real zeros."""
    oids = (SNMP_OID_INPUTS_VOLTAGE, current_oid, pf_oid)
    coordinator.data.update(
        {
            oid.replace("unit", "1").replace("index", "1"): value
            for oid, value in zip(oids, values, strict=True)
        }
    )
    sensor = entity_type(coordinator, *indices)
    assert sensor.native_value == expected
