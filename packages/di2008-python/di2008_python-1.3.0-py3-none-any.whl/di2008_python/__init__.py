"""
DATAQ DI-2008 Interface
Adapted from original DATAQ Instruments Python Interface under the MIT License

Provides an interface for configuring and reading from DI-2008 Data Acquisition Devices (DAQs)

This file is part of DI2008_Python, https://github.com/Computational-Mechanics-Materials-Lab/DI2008_Python

MIT License
"""

from .di2008_python import DI2008, print_all_di2008_metadata
from .di2008_layout_settings import (
    DI2008AnalogLayout,
    DI2008TCType,
    DI2008ADCRange,
    DI2008AnalogChannels,
    DI2008AllAnalogChannels,
    DI2008ScanRateSettings,
    DI2008FilterModes,
    DI2008PS,
    DI2008PSSettings,
    DI2008BaudRate,
    DI2008Timeout,
    DI2008SerialNums,
    DI2008HardwareID,
)

__author__ = "Clark Hensley, J. Logan Betts, and Matthew W. Priddy"
__copyright__ = "Copyright 2025"
__license__ = "MIT"
__version__ = "1.3.0"
__maintainer__ = "Clark Hensley"
__email__ = "ch3136@msstate.edu"
__status__ = "Production"

__all__ = [
    "DI2008",
    "print_all_di2008_metadata",
    "DI2008AnalogLayout",
    "DI2008TCType",
    "DI2008ADCRange",
    "DI2008AnalogChannels",
    "DI2008AllAnalogChannels",
    "DI2008ScanRateSettings",
    "DI2008FilterModes",
    "DI2008PS",
    "DI2008PSSettings",
    "DI2008BaudRate",
    "DI2008Timeout",
    "DI2008SerialNum",
    "DI2008HardwareID",
]
