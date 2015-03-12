midas
=====

TCP/IP modbus driver for [Honeywell Midas gas detectors](http://www.honeywellanalytics.com/en/products/Midas).

<p align="center">
  <img src="http://www.honeywellanalytics.com/~/media/honeywell-analytics/products/midas/images/midas.jpg" height="400" />
</p>

Installation
============

#####TODO Make pypi

You can clone and build from source:

```
git clone https://github.com/numat/midas.git
cd midas
python setup.py install
```

This depends on [pymodbus](https://github.com/bashwork/pymodbus), which is **not
compatible with Python 3**.

Usage
=====

```python
from midas import GasDetector
gas_detector = GasDetector(address="192.168.1.128", blocking=True)
print(gas_detector.get())
```

If the detector is operating at that IP address, this should return an output
a dictionary of the form:

```python
{
  "alarm_level": "none",       # Can be "none", "low", or "high"
  "concentration": 0.0,        # Current gas concentration reading
  "connected": True,           # Monitors heartbeat for connection
  "fault": "No fault",         # Can be any option in `gas_detector.fault_status_options`
  "flow": 514,                 # Flow rate, in cc / minute
  "high_alarm_threshold": 2.0, # Threshold concentration for high alarm trigger
  "life": 16027,               # Hours until cartridge replacement required
  "low_alarm_threshold": 1.0,  # Threshold concentration for low alarm trigger
  "state": "Monitoring",       # Can be any option in `gas_detector.monitoring_status_options`
  "temperature": 26,           # Detector temperature, in celsius
  "units": "ppm",              # Units for concentration values
  "url": "192.168.1.193"       # IP address of connection, can be used to link to Honeywell's own web interface
}
```

Asynchronous
============

The above example works for small numbers of gas detectors. At larger scales, the time spent waiting for detector responses is prohibitive. Asynchronous programming
allows us to send out all of our requests in parallel, and then handle responses as
they trickle in. For more information, read through
[krondo's twisted introduction](http://krondo.com/?page_id=1327).

```python
from midas import GasDetector
from twisted.internet import reactor, task

gas_detectors = [GasDetector(address="192.168.1.%d" % i, blocking=False)
                 for i in range(192, 198)]

def f():
    for gas_detector in gas_detectors:
        print(gas_detector.get())  # Grabs most recent server response
        gas_detector.update()      # Sends request for data

loop = task.LoopingCall(f)
loop.start(0.5)
reactor.run()
```

This looks more complex, but the advantages are well worth it at scale. Essentially,
`sleep`ing is replaced by scheduling functions with twisted. This allows your code
to do other things while waiting for responses.

We try hiding some of the mess of asynchronous programming here. This makes some
assumptions on use case. Namely, the `get` method is not guaranteed to be
updated by the time you read it. If this sounds like an issue for you, you can
dive into the async logic and create your own callbacks.
