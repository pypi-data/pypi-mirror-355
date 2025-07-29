"""
DATAQ DI-2008 Interface -- Layout Enumerations
Adapted from original DATAQ Instruments Python Interface under the MIT License

The DI-2008 uses a serial interface with integer values. This file declares the enumerations to describe these values

This file is part of DI2008_Python, https://github.com/Computational-Mechanics-Materials-Lab/DI2008_Python

MIT License
"""

from enum import IntEnum, Enum


class DI2008AnalogLayout(IntEnum):
    """
    Describes the connected device to each port on the DAQ
    """

    # Thermocouple
    # 0b0001000000000000
    TC = 0x1000

    # For enabling the Digital Channel
    # 0b0000000000001000
    #DI = 0x0008

    # Used as a sentinel to ignore
    # 0b1111111111111111
    IGNORE = 0xFFFF

    # Analog-Digital converter
    # Number doesn't matter, left as 0
    # 0b0000000000000000
    ADC = 0x0000


class DI2008TCType(IntEnum):
    """
    Enumerates the types of Thermocouple which the DI-2008 cna read
    """

    B = 0x0 << 8
    E = 0x1 << 8
    J = 0x2 << 8
    K = 0x3 << 8
    N = 0x4 << 8
    R = 0x5 << 8
    S = 0x6 << 8
    T = 0x7 << 8


class DI2008ADCRange(Enum):
    """
    Enumerates the voltage ranges for ADC, as well as the necessary multiplier for rescaling
    """

    mV10 = ((0x5 << 8), 0.01)
    mV25 = ((0x4 << 8), 0.025)
    mV50 = ((0x3 << 8), 0.05)
    mV100 = ((0x2 << 8), 0.1)
    mV250 = ((0x1 << 8), 0.25)
    mV500 = ((0x0 << 8), 0.5)
    V1 = ((0xD << 8), 1.0)
    V2_5 = ((0xC << 8), 2.5)
    V5 = ((0xB << 8), 5.0)
    V10 = ((0xA << 8), 10.0)
    V25 = ((0x9 << 8), 25.0)
    V50 = ((0x8 << 8), 50.0)


class DI2008AnalogChannels(IntEnum):
    """
    Enumerates the 8 Analog Channels
    """

    CH1 = 0x0
    CH2 = 0x1
    CH3 = 0x2
    CH4 = 0x3
    CH5 = 0x4
    CH6 = 0x5
    CH7 = 0x6
    CH8 = 0x7


class _DI2008AllAnalogChannels(Enum):
    """
    Denote all 8 channels, not an actual value
    """

    _instance = 0


DI2008AllAnalogChannels = _DI2008AllAnalogChannels._instance


class DI2008ScanRateSettings(Enum):
    """
    Sentinels to manage the values related to scan rate and filtering
    """

    SRATE = 0
    DEC = 1
    FILTER = 2


class DI2008FilterModes(Enum):
    """
    Values for Filtering of the DI-2008
    """

    LAST_POINT = 0
    AVERAGE = 1
    MAXIMUM = 2
    MINIMUM = 3


class _DI2008PS(Enum):
    """
    Denote that the PS is being set, not a value
    """

    _instance = 0


DI2008PS = _DI2008PS._instance


# Potential valid values for PS
class DI2008PSSettings(IntEnum):
    """
    Potential values for the PS setting
    """

    BYTES16 = 0
    BYTES32 = 1
    BYTES64 = 2
    BYTES128 = 3


class _DI2008BaudRate(Enum):
    """
    Denote that the Baud Rate is being set, not a value
    """

    _instance = 0


DI2008BaudRate = _DI2008BaudRate._instance


class _DI2008Timeout(Enum):
    """
    Denote that the timeout is being set, not a value
    """

    _instance = 0


DI2008Timeout = _DI2008Timeout._instance


class _DI2008SerialNums(Enum):
    """
    Denote that the timeout is being set, not a value
    """

    _instance = 0


DI2008SerialNums = _DI2008SerialNums._instance


class _DI2008HardwareID(Enum):
    """
    Sentinel for setting HWID
    """

    _instance = 0


DI2008HardwareID = _DI2008HardwareID._instance
