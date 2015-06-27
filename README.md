midas
=====

Python driver for
[Honeywell Midas gas detectors](http://www.honeywellanalytics.com/en/products/Midas).

<p align="center">
  <img src="http://www.honeywellanalytics.com/~/media/honeywell-analytics/products/midas/images/midas.jpg" height="400" />
</p>

Installation
============

###Device

 * Open front cover and remove internal packaging.
 * Install gas sensor cartridge and close cover.
 * Plug the device into a [PoE+](https://en.wikipedia.org/wiki/Power_over_Ethernet)-capable switch.
 * Set the IP address on the front panel in the `net` submenu.
   - If you use DHCP, set `AU Y`. Add the MAC to your routing table.
   - Otherwise, `AU N`, and then set the four address digits.
 * Reboot.
 * To test, access the device's website by typing the IP address into a browser.

###Software

```
pip install midas
```

If you don't like pip, you can also install from source:

```
git clone https://github.com/numat/midas.git
cd midas
python setup.py install
```

This depends on [pymodbus](https://github.com/bashwork/pymodbus), which is
**not compatible with Python 3**.

Usage
=====

###Command Line

To test your connection and stream real-time data, use the command-line
interface. You can read the state with

```
$ midas 192.168.1.192
{
  "alarm": "none",
  "concentration": 0.0,
  "connected": true,
  "fault": "No fault",
  "flow": 508,
  "high-alarm threshold": 2.0,
  "ip": "192.168.1.192",
  "life": 538.96,
  "low-alarm threshold": 1.0,
  "state": "Monitoring",
  "temperature": 26,
  "units": "ppm"
}
```

or stream a table of data with the `--stream` flag. See `midas --help`
for more.

###Python

For more complex behavior, you can write a python script to interface with
other sensors and actuators.

```python
from midas import GasDetector
gas_detector = GasDetector(ip_address='192.168.1.192')
print(gas_detector.get())
```

If the detector is operating at that IP address, this should return an output
a dictionary of the form:

```python
{
  'alarm': 'none',             # Can be 'none', 'low', or 'high'
  'concentration': 0.0,        # Current gas concentration reading
  'connected': True,           # Monitors heartbeat for connection
  'fault': 'No fault',         # Can be any option in `gas_detector.fault_status_options`
  'flow': 514,                 # Flow rate, in cc / minute
  'high-alarm threshold': 2.0, # Threshold concentration for high alarm trigger
  'ip': '192.168.1.192',       # IP address of connection, can be used to link to Honeywell's own web interface
  'life': 538.95,              # Days until cartridge replacement required
  'low-alarm threshold': 1.0,  # Threshold concentration for low alarm trigger
  'state': 'Monitoring',       # Can be any option in `gas_detector.monitoring_status_options`
  'temperature': 26,           # Detector temperature, in celsius
  'units': 'ppm'               # Units for concentration values
}
```

###Asynchronous

The above example works for small numbers of gas detectors. At larger scales,
the time spent waiting for detector responses is prohibitive. Asynchronous
programming allows us to send out all of our requests in parallel, and then
handle responses as they trickle in. For more information, read through
[krondo's twisted introduction](http://krondo.com/?page_id=1327).

```python
from midas import GasDetector
from twisted.internet import reactor, task

# As an example, assume we have six detectors in 192.168.1.[192-197].
gas_detectors = [GasDetector('192.168.1.{}'.format(i)) for i in range(192, 198)]

def on_response(response):
    """This function gets run whenever a device responds."""
    print(response)

def loop():
    """This function will be called in an infinite loop by twisted."""
    for detector in gas_detectors:
        detector.get(on_response)

loop = task.LoopingCall(loop)
loop.start(0.5)
reactor.run()
```

This looks more complex, but the advantages are well worth it at scale.
Essentially, sleeping is replaced by scheduling functions with twisted. This
allows your code to do other things while waiting for responses, letting you
scale to thousands of devices.
