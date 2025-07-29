# DI2008-Python

## About
Interface for the DI-2008 in Python.

Python 3.10+

Modified from original interface in Python by DATAQ Instruments under MIT License

Maintainer: Clark Hensley ch3136@msstate.edu

## Getting Started
Install via pip from PyPI:
```sh
pip install di2008-python
```

See Available DI-2008s:
```py
from di2008_python import print_all_di2008_metadata
print_all_di2008_metadata()
```

Instantiate DI2008 Object with Dictionary of Parameters:
```py
from di2008_python import (
    DI2008,
    DI2008AnalogChannels,
    DI2008AllAnalogChannels,
    DI2008AnalogLayout,
    DI2008TCType,
    DI2008ScanRateSettings,
    DI2008FilterModes,
    DI2008SerialNums
)

# Create an array of DI-2008s with relevant settings
di2008_array = DI2008({
        # Global Settings
        DI2008AllAnalogChannels: (DI2008AnalogLayout.TC, DI2008TCType.K),
        DI2008ScanRateSettings.SRATE: 4,
        DI2008ScanRateSettings.DEC: 1,
        DI2008ScanRateSettings.FILTER: {
            DI2008AllAnalogChannels: DI2008FilterModes.AVERAGE,
            },
        # Serial Numbers of DI-2008s to apply
        DI2008lSerialNums: [<DI-2008 Serial Num>, <DI-2008 Serial Num>, ...],
        # Overwriting settings for a given DI-2008 (Not one of the ones listed above)
        <DI-2008 Serial Num>: {
            DI2008AnalogChannels.CH1: (DI2008AnalogLayout.TC, DI2008TCType.N),
            DI2008ScanRateSettings.FILTER: {
                DI2008AnalogChannels.CH1: DI2008FilterModes.LAST_POINT,
                }
            }

# Synchronized start of DI2008s
di2008_array.start_di2008s()

# Read from the DI2008s
while True:
    data = di2008_array.read_di2008s()
    print(data)
```

This interface uses named enumerations to ensure that what settings are being used is clear and concise

Currently, this package supports configuring and using up to 16 DI-2008s via ChannelStretch synchronization, and using any configuration of the Analog Channels. As of version 1.2.2, the digital channels, as well as the Event, Record, Rate, and Count channels are not yet supported.

*Note About Bandwidth:*
Per the DI-2008 Protocol, if a single analog channel is enabled, the maximum sample rate of the DI-2008 is 2000 Hz, and if two or more analog channels are enabled, the maximum sample rate of the DI-2008 is 200 Hz. However, in this current implementation, that rate must be again divided by the number of enabled channels. Thus, 2 channels have a maximum sample rate of 100 Hz, and all 8 enabled channels can be sampled at, at most, 25 Hz. This is a known issue and work to address it is ongoing.

## Current Features:
* Thermocouples
* ADC Reading
* Changing Scan Rate, Decimation, and Filtering Mode
* Automatic ChannelStretch Synchronized Initialization
* Enforce cleanup on stopping
* Changing Packet Size
* Interface with the `info` operator

## Planned Features:
* Reading configuration from .json/.toml files as well as raw Python dictionaries
* Digital Channels
* Specify Digital Input as well as Output
* CJCDelta
* Rate Measurement
* LED Color

Further information about the DI-2008 can be found on [DATAQ's website](https://www.dataq.com/products/di-2008) and via the [DI-2008 Protocol](https://www.dataq.com/resources/pdfs/misc/di-2008%20protocol.pdf).
