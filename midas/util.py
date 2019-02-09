"""Base functionality for modbus communication.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""
import asyncio

from pymodbus.client.asynchronous.asyncio import ReconnectingAsyncioModbusTcpClient


class AsyncioModbusClient(object):
    """A generic asyncio client.

    This expands upon the pymodbus ReconnectionAsyncioModbusTcpClient by
    including standard timeouts, async context manager, and queued requests.
    """

    def __init__(self, address, timeout=1):
        """Set up communication parameters."""
        self.ip = address
        self.timeout = timeout
        self.client = ReconnectingAsyncioModbusTcpClient()
        self.open = False
        self.waiting = False

    async def __aenter__(self):
        """Asynchronously connect with the context manager."""
        await self._connect()
        return self

    async def __aexit__(self, *args):
        """Provide exit to the context manager."""
        self._close()

    async def _connect(self):
        """Start asynchronous reconnect loop."""
        self.waiting = True
        await self.client.start(self.ip)
        self.waiting = False
        if self.client.protocol is None:
            raise IOError("Could not connect to '{}'.".format(self.ip))
        self.modbus = self.client.protocol
        self.open = True

    async def _request(self, function, args):
        """Send a request to the device and awaits a response.

        This mainly ensures that requests are sent serially, as the Modbus
        protocol does not allow simultaneous requests (it'll ignore any
        request sent while it's processing something). The driver handles this
        by assuming there is only one client instance. If other clients
        exist, other logic will have to be added to either prevent or manage
        race conditions.
        """
        while self.waiting:
            await asyncio.sleep(0.1)
        if not self.open:
            await self._connect()
        if not self.open:
            raise TimeoutError("Not connected to device.")
        try:
            future = function(*args)
        except AttributeError:
            raise TimeoutError("Not connected to device.")
        self.waiting = True
        try:
            return await asyncio.wait_for(future, timeout=self.timeout)
        except asyncio.TimeoutError as e:
            if self.open:
                # This came from reading through the pymodbus@python3 source
                # Problem was that the driver was not detecting disconnect
                self.client.protocol_lost_connection(self.modbus)
                self.open = False
            raise TimeoutError(e)
        finally:
            self.waiting = False

    def _close(self):
        """Close the TCP connection."""
        self.client.stop()
        self.open = False
        self.waiting = False
