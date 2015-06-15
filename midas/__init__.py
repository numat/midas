#!/usr/bin/python
"""
A Python driver for Honeywell's Midas gas detector, using TCP/IP modbus.

Distributed under the GNU General Public License v2
Copyright (C) 2015 NuMat Technologies
"""
from struct import pack
from time import time
import logging

from pymodbus.client.async import ModbusClientProtocol
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder

from twisted.internet import reactor, protocol


class GasDetector(object):
    """Python driver for [Honeywell Midas Gas Detector](http://www.honeywell
    analytics.com/en/products/Midas).

    This driver uses twisted + tornado-twisted bridge to asynchronously
    read from the sensor. In order to decouple this interface from the core
    event loop, this class doesn't communicate with clients directly. Rather,
    `update()` sends a request, and `get()` returns the most recent server
    response. These methods should be used with an external async event loop.
    """
    # Map register bits to sensor states
    # Further information can be found in the Honeywell Midas technical manual
    monitor_state_options = ["Warmup",
                             "Monitoring",
                             "Monitoring with alarms inhibited",
                             "Monitoring with alarms and faults inhibited",
                             "Monitoring every response inhibited",
                             "Alarm or fault simulation",
                             "Bump test mode",
                             "4-20 mA loop calibration mode",
                             "Non-analog calibration mode"]
    fault_status_options = ["No fault",
                            "Maintenance fault",
                            "Instrument fault",
                            "Maintenance and instrument faults"]
    concentration_unit_options = ["ppm", "ppb", "% volume", "% LEL", "mA"]
    alarm_level_options = ["none", "low", "high"]

    def __init__(self, address, blocking=False, timeout=2):
        """Connects to modbus on initialization."""
        self.client = None
        self.last_response = time()
        self.address = address
        self.blocking = blocking
        self.timeout = timeout
        self.connected = False
        self._connect()

    def update(self):
        """Sends a request for sensor concentration."""
        if self.blocking:
            raise Exception("GasDetector.update not available while blocking.")
        if not self.client or time() - self.last_response > self.timeout:
            self.client = None
            self.connected = False
            self._connect()
        else:
            deferred = self.client.read_holding_registers(address=0, count=16)
            deferred.addCallbacks(self._on_response, self._on_error)

    def get(self):
        """Returns the most recently received sensor state."""
        if self.blocking:
            result = self.client.read_holding_registers(address=0, count=16)
            self._on_response(result)
        if not hasattr(self, "concentration"):
            return {"url": self.address, "connected": self.connected}
        return {"concentration": self.concentration,
                "units": self.units,
                "state": self.monitor_state,
                "fault": self.fault_status,
                "temperature": self.temperature,
                "life": self.cell_life,
                "flow": self.flow_rate,
                "alarm_level": self.alarm_level,
                "low_alarm_threshold": self.low_alarm_threshold,
                "high_alarm_threshold": self.high_alarm_threshold,
                "url": self.address,
                "connected": self.connected}

    def _connect(self):
        """Initializes modbus connection through twisted framework."""
        if self.blocking:
            self.client = ModbusTcpClient(self.address)
            self.connected = self.client.connect()
        else:
            deferred = protocol.ClientCreator(reactor, ModbusClientProtocol
                                              ).connectTCP(self.address, 502)
            deferred.addCallbacks(self._on_connection, self._on_error)

    def _on_connection(self, client):
        """Saves reference to client on connection."""
        self.client = client
        self.connected = True
        self.last_response = time()
        self.update()

    def _on_response(self, result):
        """Parses the response and saves state to this object."""
        self.connected = True
        self.last_response = time()

        register_bytes = "".join(pack("<H", x) for x in result.registers)
        decoder = BinaryPayloadDecoder(register_bytes)

        # Register 40001 is a collection of alarm status signals
        reg_40001 = decoder.decode_bits() + decoder.decode_bits()
        # Bits 0-3 map to the monitor state
        monitor_integer = sum(1 << i for i, b in enumerate(reg_40001[:4]) if b)
        self.monitor_state = self.monitor_state_options[monitor_integer]
        # Bits 4-5 map to fault status
        fault_integer = sum(1 << i for i, b in enumerate(reg_40001[4:6]) if b)
        self.fault_status = self.fault_status_options[fault_integer]
        # Bits 6 and 7 tell if low and high alarms are active
        low, high = reg_40001[6:8]
        self.alarm_level = self.alarm_level_options[low + high]
        # Bits 8-10 tell if internal sensor relays 1-3 are energized
        self.relays_energized = reg_40001[8:11]
        # Bit 11 is a heartbeat bit that toggles every two seconds. Skipping.
        # Bit 12 tells if relays are under modbus control. Skipping.
        # Remaining bits are empty. Skipping.

        # Register 40002 has a gas ID and a sensor cartridge ID. Skipping.
        decoder._pointer += 2

        # Registers 40003-40004 are the gas concentration as a float
        self.concentration = decoder.decode_32bit_float()

        # Register 40005 is the concentration as an int. Skipping.
        # Register 40006 is the number of the most important fault. Skipping.
        # Register 40007 has info related to 40005 in the first byte. Skipping.
        decoder._pointer += 5

        # Register 40007 holds the concentration unit in the second byte
        # Instead of being an int, it's the position of the up bit
        unit_bits = decoder.decode_bits()
        self.units = self.concentration_unit_options[unit_bits.index(True)]

        # Register 40008 holds the sensor temperature in Celsius
        self.temperature = decoder.decode_16bit_int()

        # Register 40009 holds number of hours remaining in cell life
        self.cell_life = decoder.decode_16bit_uint()

        # Register 40010 holds the number of heartbeats (16 LSB). Skipping.
        decoder._pointer += 2

        # Register 40011 is the sample flow rate in cc / min
        self.flow_rate = decoder.decode_16bit_uint()

        # Register 40012 is blank. Skipping.
        decoder._pointer += 2

        # Registers 40013-40016 are the alarm concentration thresholds
        self.low_alarm_threshold = decoder.decode_32bit_float()
        self.high_alarm_threshold = decoder.decode_32bit_float()

        # Despite what the manual says, thresholds are always reported in ppm.
        # Let's fix that to match the concentration units.
        if self.units == "ppb":
            self.concentration *= 1000
            self.low_alarm_threshold *= 1000
            self.high_alarm_threshold *= 1000

    def _on_error(self, error):
        logging.log(logging.ERROR, error)
        self._connect()


def command_line():
    import argparse
    import json
    from time import time

    parser = argparse.ArgumentParser(description="Read a Honeywell Midas gas "
                                     "detector state from the command line.")
    parser.add_argument("address", help="The IP address of the gas detector.")
    parser.add_argument("--stream", "-s", action="store_true",
                        help="Sends a constant stream of detector data, "
                             "formatted as a tab-separated table.")
    args = parser.parse_args()

    detector = GasDetector(args.address, blocking=True)

    if args.stream:
        try:
            print("time\tconcentration\tunits\talarm level\tstate\tfault\t"
                  "temperature (C)\tflow rate (cc/min)\tlow alarm threshold\t"
                  "high alarm threshold")
            t0 = time()
            while True:
                d = detector.get()
                if d["connected"]:
                    print(("{time:.2f}\t{concentration:.1f}\t{units}\t"
                           "{alarm_level}\t{state}\t{fault}\t{temperature:.1f}"
                           "\t{flow:.1f}\t{low_alarm_threshold:.1f}\t"
                           "{high_alarm_threshold:.1f}"
                           ).format(time=time()-t0, **d))
                else:
                    print("Not connected")
        except KeyboardInterrupt:
            pass
    else:
        print(json.dumps(detector.get(), indent=2, sort_keys=True))


if __name__ == "__main__":
    command_line()
