#!/usr/bin/python
"""
A Python driver for Honeywell's Midas gas detector, using TCP/IP modbus.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""
import csv
import os

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from midas.util import AsyncioModbusClient

root = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(root, 'faults.csv')) as in_file:
    reader = csv.reader(in_file)
    next(reader)
    faults = {row[0]: {'description': row[1], 'condition': row[2],
                       'recovery': row[3]} for row in reader}

options = {
    'alarm level': [
        'none',
        'low',
        'high'
    ],
    'concentration unit': [
        'ppm',
        'ppb',
        '% volume',
        '% LEL',
        'mA'
    ],
    'monitor state': [
        'Warmup',
        'Monitoring',
        'Monitoring with alarms inhibited',
        'Monitoring with alarms and faults inhibited',
        'Monitoring every response inhibited',
        'Alarm or fault simulation',
        'Bump test mode',
        '4-20 mA loop calibration mode',
        'Non-analog calibration mode'
    ],
    'fault status': [
        'No fault',
        'Maintenance fault',
        'Instrument fault',
        'Maintenance and instrument faults'
    ]
}


class GasDetector(AsyncioModbusClient):
    """Python driver for Honeywell Midas Gas Detectors.

    This driver handles asynchronous Modbus TCP/IP and Midas parsing,
    returning a human-readable dictionary. In particular, this loads fault
    and boolean information specified in the manual and looks up codes so
    you don't have to.
    """

    async def get(self) -> dict:
        """Get current state from the Midas gas detector."""
        return self._parse(await self.read_registers(0, 16))

    async def reset_alarms_and_faults(self) -> None:
        """Reset all alarms and faults."""
        return await self.write_registers(20, (0x015E, 0x3626))

    async def inhibit_alarms(self) -> None:
        """Inhibit alarms from triggering."""
        return await self.write_registers(20, (0x025E, 0x3626))

    async def inhibit_alarms_and_faults(self) -> None:
        """Inhibit alarms and faults from triggering."""
        return await self.write_registers(20, (0x035E, 0x3626))

    async def remove_inhibit(self) -> None:
        """Cancel the inhibit state."""
        return await self.write_registers(20, (0x055E, 0x3626))

    def _parse(self, registers: list) -> dict:
        """Parse the response, returning a dictionary."""
        result: dict = {'ip': self.ip, 'connected': True}
        bigendian = Endian.BIG if self.pymodbus35plus else Endian.Big  # type:ignore[attr-defined]
        lilendian = Endian.LITTLE if self.pymodbus35plus else Endian.Little  # type:ignore
        decoder = BinaryPayloadDecoder.fromRegisters(registers,
                                                     byteorder=bigendian,
                                                     wordorder=lilendian)
        # Register 40001 is a collection of alarm status signals
        b = [decoder.decode_bits(), decoder.decode_bits()]
        reg_40001 = b[1] + b[0]
        # Bits 0-3 map to the monitor state
        monitor_integer = sum(1 << i for i, b in enumerate(reg_40001[:4]) if b)
        result['state'] = options['monitor state'][monitor_integer]
        # Bits 4-5 map to fault status
        fault_integer = sum(1 << i for i, b in enumerate(reg_40001[4:6]) if b)
        result['fault'] = {'status': options['fault status'][fault_integer]}
        # Bits 6 and 7 tell if low and high alarms are active
        low, high = reg_40001[6:8]
        result['alarm'] = options['alarm level'][low + high]
        # Bits 8-10 tell if internal sensor relays 1-3 are energized. Skipping.
        # Bit 11 is a heartbeat bit that toggles every two seconds. Skipping.
        # Bit 12 tells if relays are under modbus control. Skipping.
        # Remaining bits are empty. Skipping.
        # Register 40002 has a gas ID and a sensor cartridge ID. Skipping.
        decoder._pointer += 2
        # Registers 40003-40004 are the gas concentration as a float
        result['concentration'] = decoder.decode_32bit_float()
        # Register 40005 is the concentration as an int. Skipping.
        decoder._pointer += 2
        # Register 40006 is the number of the most important fault.
        fault_number = decoder.decode_16bit_uint()
        if fault_number != 0:
            code = ('m' if fault_number < 30 else 'F') + str(fault_number)
            result['fault']['code'] = code
            result['fault'].update(faults[code])
        # Register 40007 holds the concentration unit in the second byte
        # Instead of being an int, it's the position of the up bit
        unit_bit = decoder.decode_bits().index(True)
        result['units'] = options['concentration unit'][unit_bit]
        decoder._pointer += 1
        # Register 40008 holds the sensor temperature in Celsius
        result['temperature'] = decoder.decode_16bit_int()
        # Register 40009 holds number of hours remaining in cell life
        result['life'] = decoder.decode_16bit_uint() / 24.0
        # Register 40010 holds the number of heartbeats (16 LSB). Skipping.
        decoder._pointer += 2
        # Register 40011 is the sample flow rate in cc / min
        result['flow'] = decoder.decode_16bit_uint()
        # Register 40012 is blank. Skipping.
        decoder._pointer += 2
        # Registers 40013-40016 are the alarm concentration thresholds
        result['low-alarm threshold'] = round(decoder.decode_32bit_float(), 6)
        result['high-alarm threshold'] = round(decoder.decode_32bit_float(), 6)
        # Despite what the manual says, thresholds are always reported in ppm.
        # Let's fix that to match the concentration units.
        if result['units'] == 'ppb':
            result['concentration'] *= 1000
            result['low-alarm threshold'] *= 1000
            result['high-alarm threshold'] *= 1000
        return result
