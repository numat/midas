#!/usr/bin/python
"""
A Python driver for Honeywell's Midas gas detector, using TCP/IP modbus.

Distributed under the GNU General Public License v2
Copyright (C) 2019 NuMat Technologies
"""
from typing import Any

from midas.driver import GasDetector


def command_line(args: Any = None) -> None:
    """Command-line tool for Midas gas detector communication."""
    import argparse
    import asyncio
    import json

    parser = argparse.ArgumentParser(description="Read a Honeywell Midas gas "
                                     "detector state from the command line.")
    parser.add_argument('address', help="The IP address of the gas detector.")
    args = parser.parse_args(args)

    async def get() -> None:
        async with GasDetector(args.address) as detector:
            print(json.dumps(await detector.get(), indent=4, sort_keys=True))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(get())
    loop.close()


if __name__ == '__main__':
    command_line()
