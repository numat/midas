"""Test the driver correctly responds with correct data."""
from unittest import mock

import pytest

from midas import command_line
from midas.mock import GasDetector


@pytest.fixture
def midas_driver():
    """Confirm the driver correctly initializes."""
    return GasDetector('fake ip')


@pytest.fixture
def expected_data():
    """Return the inital mocked data format."""
    return {
        "ip": "192.168.0.1",
        "connected": True,
        "state": "Monitoring",
        "fault": {"status": "No fault"},
        "alarm": "none",
        "concentration": 0,
        "units": "ppm",
        "temperature": 30,
        "life": 556.0833333333334,
        "flow": 482,
        "low-alarm threshold": 5,
        "high-alarm threshold": 8,
    }


@mock.patch("midas.GasDetector", GasDetector)
def test_driver_cli(capsys):
    """Confirm the commandline interface works."""
    command_line(["fakeip"])
    captured = capsys.readouterr()
    assert "Monitoring" in captured.out


def test_driver_cli_timeout():
    """Confirm the commandline raises an error on failure to connect."""
    with pytest.raises(TimeoutError):
        command_line(["fakeip"])


@pytest.mark.asyncio
async def test_get(midas_driver, expected_data):
    """Confirm that the driver returns correct values on get() calls."""
    assert expected_data == await midas_driver.get()


@pytest.mark.asyncio
async def test_inhibit_roundtrip(midas_driver, expected_data):
    """Test a roundtrip with the driver using inhibit/uninhibit."""
    await midas_driver.inhibit_alarms()
    state = await midas_driver.get()
    assert state == {**expected_data, "state": "Monitoring with alarms inhibited"}
    await midas_driver.remove_inhibit()
    state = await midas_driver.get()
    assert state == expected_data
