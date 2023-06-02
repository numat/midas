"""Mock Midas interface. Use for debugging systems."""

import asyncio
from random import random
from typing import Any
from unittest.mock import MagicMock

from midas.driver import GasDetector as realGasDetector


class AsyncClientMock(MagicMock):
    """Magic mock that works with async methods."""

    async def __call__(self, *args, **kwargs):  # type: ignore
        """Convert regular mocks into into an async coroutine."""
        return super().__call__(*args, **kwargs)

    def close(self) -> None:
        """Close the connection."""
        ...


class GasDetector(realGasDetector):
    """Mock interface to the Midas gas detector."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set an inital mocked state."""
        self.client = AsyncClientMock()
        self.state = {
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

    def __getattr__(self, attr):  # type: ignore
        """Return False for any undefined method."""

        def handler(*args, **kwargs):  # type: ignore
            return False

        return handler

    async def get(self) -> dict:
        """Return a mock state with the same object structure."""
        await asyncio.sleep(random() * 0.1)
        return self.state

    async def inhibit_alarms(self) -> None:
        """Inhibit alarms from triggering."""
        self.state["state"] = "Monitoring with alarms inhibited"

    async def remove_inhibit(self) -> None:
        """Cancel the inhibit state."""
        self.state["state"] = "Monitoring"
