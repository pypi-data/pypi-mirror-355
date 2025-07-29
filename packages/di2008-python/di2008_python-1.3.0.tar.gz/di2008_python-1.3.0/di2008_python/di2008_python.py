"""
DATAQ DI-2008 Interface
Adapted from original DATAQ Instruments Python Interface under the MIT License

Provides an interface for configuring and reading from DI-2008 Data Acquisition Devices (DAQs)

This file is part of DI2008_Python, https://github.com/Computational-Mechanics-Materials-Lab/DI-2008-Driver

MIT License
"""

import time
import serial
import serial.tools.list_ports

from typing import Callable, TypeAlias, Any, Final

import weakref

# Enumerations for DI-2008 Settings
from .di2008_layout_settings import (
    DI2008AnalogLayout,
    DI2008TCType,
    DI2008ADCRange,
    DI2008AnalogChannels,
    DI2008AllAnalogChannels,
    _DI2008AllAnalogChannels,
    DI2008ScanRateSettings,
    DI2008FilterModes,
    DI2008PS,
    DI2008PSSettings,
    DI2008BaudRate,
    DI2008Timeout,
    DI2008SerialNums,
    DI2008HardwareID,
)


def print_all_di2008_metadata(hwid: str = "USB VID:PID=0683") -> None:
    """
    Print out the information of all found DI-2008s on given hwid
    hwid: str, the target hwid (default "USB VID:PID=0683")
    """
    port: serial.tools.list_ports_linux.SysFS
    for port in serial.tools.list_ports.comports():
        # Find All DI-2008s by hardware ID
        if hwid in port.hwid:
            assert port.location is not None
            scw: SerialConnectionWrapper = SerialConnectionWrapper(
                port.location,
                serial.Serial(port.device, 115200, timeout=0.0),
            )
            scw.send_command("stop")

            info_0: str | None = scw.echo("info 0")
            assert info_0 is not None
            info_0 = info_0.split("info 0 ")[1]

            info_1: str | None = scw.echo("info 1")
            assert info_1 is not None
            info_1 = info_1.split("info 1 ")[1]

            info_2: str | None = scw.echo("info 2")
            assert info_2 is not None
            info_2 = info_2.split("info 2 ")[1]

            info_6: str | None = scw.echo("info 6")
            assert info_6 is not None
            info_6 = info_6.split("info 6 ")[1]

            info_9: str | None = scw.echo("info 9")
            assert info_9 is not None
            info_9 = info_9.split("info 9 ")[1]

            print(f'''Info 0: {info_0} (Always returns "DATAQ")
Info 1: {info_1} (Device PID, should be "2008")
Info 2: {int(info_2, base=16) / 100} (Device Firmware Version)
Info 6: {hex(int(info_6, base=16))} (Device Serial Number)
Info 9: {info_9} (Current Sample Rate Divisor)\n''')
            scw.close()


class _DI2008Port:
    """
    Structure Class
    Stores a single port with:
    channel number (channel: int)
    port layout (layout: int)
    type of connected device (connected_type: int)
    sclaing function (rescalar: Callable[[int], float])
    """

    def __init__(
        self,
        channel: DI2008AnalogChannels,
        layout: int,
        connected_type: int,
        rescalar: Callable[[int], float],
    ) -> None:
        """
        _DI2008Port Init Signature:
        channel: int
        layout: int
        connected_type: int
        rescalar: Callable[[int], float]
        """
        self.channel: int = channel
        self.layout: int = layout
        self.connected_type: int = connected_type
        self.rescalar: Callable[[int], float] = rescalar


class SerialConnectionWrapper:
    """
    Wraps around a pyserial serial connection
    Automatically encodes and decodes communication.
    Stores:
    the connected DI-2008's hardware map location (location: str)
    the actual connection (conn: serial.Serial)
    the connection's serial number (serial_num: int)
    a list of port configurations (ports: list[_DI2008Port])
    """

    def __init__(self, location: str, connection: serial.Serial) -> None:
        """
        SerialConnectionWrapper Signature:
        location: str
        connection: serial.Serial
        """
        self.location: str = location
        self.conn: serial.Serial = connection
        self.serial_num: int | None = None
        self.ports: list[_DI2008Port] | None = None

    def send_command(self, command: str) -> None:
        """Send a command without echoing"""
        self._send_command(command)

    def echo(self, command: str) -> str | None:
        """Send a command and echo the result"""
        return self._send_command(command)

    def close(self) -> None:
        """Close the serial connection"""
        self.conn.close()

    def _send_command(self, command: str) -> str | None:
        """Internal method for formatting, sending, and receiving DI2008 communication"""
        formatted_command: str = f"{command}\r"
        self.conn.write(formatted_command.encode())
        time.sleep(0.1)
        final: str = ""
        # If the `start` command was sent, the DI-2008 will immediately start sending data, which this method should not handle
        if command == "start" or command.startswith("syncstart"):
            return None
        # If we haven't started, clear the buffer and potentially return it
        else:
            while self.conn.in_waiting > 0:
                res_b: bytes = self.conn.readline()
                res: str = res_b.decode()
                # Replace newlines and non-printable characters
                res = res.replace("\n", "")
                res = res.replace("\r", "")
                res = res.replace(chr(0), "")
                final += res

            # Attemping to flush regularly to stop the stop 01 error.
            self.conn.flush()
            return final


class _DI2008Instance:
    """
    DI2008 Python Interface
    When provided input parameters, automatically contacts and configures all requested DI-2008s
    Can then be used to read from connected DI-2008
    """

    def __init__(
        self,
        serial_num: int,
        di2008_layout_dict: dict[Any, Any] | None = None,
        global_config: dict[Any, Any] | None = None,
    ) -> None:
        """
        DI2008 Signature:
        serial_num: int (The serial number of this DI-2008)
        di2008_layout_dict: dict (Dictionary of DI-2008 Serial Nums to settings. See README for more details)
        global_config: dict (Dictionary of global configs applied to all connected DI-2008s)
        """

        self.serial_num: int = serial_num
        self.di2008_layout_dict: dict[Any, Any]
        if di2008_layout_dict:
            self.di2008_layout_dict = di2008_layout_dict
        else:
            self.di2008_layout_dict = {}

        self.global_config: dict[Any, Any]
        if global_config:
            self.global_config = global_config
        else:
            self.global_config = {}

        # This order so that local things overwrite global things
        self.global_config.update(self.di2008_layout_dict)
        self.di2008_layout_dict = self.global_config

        self.target_hwid = self.di2008_layout_dict.pop(
            DI2008HardwareID, "USB VID:PID=0683"
        )
        self.baud_rate = self.di2008_layout_dict.pop(DI2008BaudRate, 115200)
        self.timeout = self.di2008_layout_dict.pop(DI2008Timeout, 0.0)

        self.scw: SerialConnectionWrapper | None = None
        self.target_hwid: str
        self.baud_rate: int
        self.timeout: float

        self.tc_rescalars: dict[DI2008TCType, Callable[[int], float]] = {
            DI2008TCType.B: self._tc_b,
            DI2008TCType.E: self._tc_e,
            DI2008TCType.J: self._tc_j,
            DI2008TCType.K: self._tc_k,
            DI2008TCType.N: self._tc_n,
            DI2008TCType.R: self._tc_r_s,
            DI2008TCType.S: self._tc_r_s,
            DI2008TCType.T: self._tc_t,
        }

        weakref.finalize(self, self._cleanup)

        # Locate selected DI-2008s
        self.find_di2008s()
        # Set selected DI-2008s
        self.configure_di2008s()

    def _cleanup(self) -> None:
        """
        Ensure that the serial socket is closed when this object is garbage-collected
        """
        if self.scw is not None:
            self.scw.send_command("stop")
            self.scw.close()

    def print_di2008_info(self) -> None:
        """
        Get the info metadata about the connected DI-2008
        """
        assert self.scw is not None

        info_0: str | None = self.scw.echo("info 0")
        assert info_0 is not None
        info_0 = info_0.split("info 0 ")[1]

        info_1: str | None = self.scw.echo("info 1")
        assert info_1 is not None
        info_1 = info_1.split("info 1 ")[1]

        info_2: str | None = self.scw.echo("info 2")
        assert info_2 is not None
        info_2 = info_2.split("info 2 ")[1]

        info_6: str | None = self.scw.echo("info 6")
        assert info_6 is not None
        info_6 = info_6.split("info 6 ")[1]

        info_9: str | None = self.scw.echo("info 9")
        assert info_9 is not None
        info_9 = info_9.split("info 9 ")[1]

        print(f'''Info 0: {info_0} (Always returns "DATAQ")
Info 1: {info_1} (Device PID, should be "2008")
Info 2: {int(info_2, base=16) / 100} (Device Firmware Version)
Info 6: {hex(int(info_6, base=16))} (Device Serial Number)
Info 9: {info_9} (Current Sample Rate Divisor)''')

    def find_di2008s(self) -> None:
        """
        Given the list of DI-2008 serial nums in the input dict, find these and generate their correct configurations
        """
        port: serial.tools.list_ports_linux.SysFS
        for port in serial.tools.list_ports.comports():
            # Find All DI-2008s by hardware ID
            if self.target_hwid in port.hwid:
                assert port.location is not None
                scw: SerialConnectionWrapper = SerialConnectionWrapper(
                    port.location,
                    serial.Serial(port.device, self.baud_rate, timeout=self.timeout),
                )
                # Stop DI-2008s first, as they are found
                scw.send_command("stop")

                # Getting Serial numbers is not ideal. Must use string echo interface
                serial_num_str: str | None = scw.echo("info 6")
                if serial_num_str is not None:
                    serial_num: str
                    try:
                        # Split off the command sent
                        serial_num = serial_num_str.split("info 6 ")[1]
                    except IndexError as e:
                        raise IndexError(
                            f"Could not get serial number for this DI-2008, with error {e}"
                        ) from e

                    # If you got the serial num, parse the string and store it in hex
                    serial_num = serial_num[0:8]
                    scw.serial_num = int(serial_num, base=16)
                    if self.serial_num != scw.serial_num:
                        scw.close()
                        continue

                else:
                    # If there is not Serial Num, likely you'll have to unplug/replug devices and try again
                    raise RuntimeError(
                        "COULD NOT GET DI-2008 SERIAL NUM! UNPLUG/REPLUG DI-2008s AND TRY AGAIN!!!"
                    )

                # Now, we check if the serial number was requested and, if so, create the configuration and make the connection.

                assert self.serial_num == scw.serial_num
                # Use the input data to get the configuration and save the connection.
                scw_ports: list[_DI2008Port] = self.get_scw_port_configuration(
                    self.di2008_layout_dict
                )
                assert scw_ports is not None
                scw.ports = scw_ports
                self.scw = scw
                break

        # If not DI-2008s were connected to
        if self.scw is None:
            raise Exception(f"Could not get DI-2008 for serial number: {self.serial_num}")

    def configure_di2008s(self) -> None:
        """
        Once the configuration for the DI-2008s has been created, input them
        """
        # Get the layout for this specific connection
        assert self.scw is not None

        # Check for a given ps value. If not, set to 0 (16 bytes)
        ps_value: DI2008PSSettings | None
        if ps_value := self.di2008_layout_dict.get(DI2008PS):
            self.scw.send_command(f"ps {ps_value}")

        else:
            self.scw.send_command(f"ps {DI2008PSSettings.BYTES16}")

        # Check for an srate value. If not, set to 4
        srate_value: int | None
        if srate_value := self.di2008_layout_dict.get(DI2008ScanRateSettings.SRATE):
            if not (4 <= srate_value <= 2232):
                raise RuntimeError(
                    f"srate value for DI-2008 with Serial Number {self.serial_num} was not between 4 and 2232, but was instead {srate_value}"
                )
            else:
                self.scw.send_command(f"srate {srate_value}")

        else:
            self.scw.send_command("srate 4")

        # Check for a decimation value, if not, set to 1
        dec_value: int | None
        if dec_value := self.di2008_layout_dict.get(DI2008ScanRateSettings.DEC):
            if not (1 <= dec_value <= 32767):
                raise RuntimeError(
                    f"dec value for DI-2008 with Serial Number {self.serial_num} was not between 1 and 32767, but was instead {srate_value}"
                )
            else:
                self.scw.send_command(f"dec {dec_value}")

        else:
            self.scw.send_command("dec 1")

        # See if filter settings are given
        channel_filter_dict: dict[DI2008AnalogChannels, DI2008FilterModes] | None
        if channel_filter_dict := self.di2008_layout_dict.get(
            DI2008ScanRateSettings.FILTER
        ):
            key: DI2008AnalogChannels
            val: DI2008FilterModes | None
            filter_default: Any = channel_filter_dict.pop(DI2008AllAnalogChannels, None)
            for key in DI2008AnalogChannels:
                val = channel_filter_dict.get(key, filter_default)
                if val is not None:
                    self.scw.send_command(f"filter {key} {val}")

        # Finally, do the slist settings generated in the last step to this DI-2008.
        assert self.scw.ports is not None
        port: _DI2008Port
        for port in self.scw.ports:
            self.scw.send_command(f"slist {port.channel} {port.layout}")

    def start(self) -> None:
        """
        Start the DI-2008 as an individual unit. Should NOT be used if multiple DI-2008s are connected in one array.
        """
        assert self.scw is not None
        self.scw.send_command("start")

    def get_scw_port_configuration(
        self, layout_input: dict[Any, Any]
    ) -> list[_DI2008Port]:
        """
        Given the dict of a desired layout, configure it into the needed values in order
        """
        ports: list[_DI2008Port] = []
        layout: (
            DI2008AnalogLayout
            | tuple[DI2008AnalogLayout, DI2008TCType | DI2008ADCRange]
            | None
        )

        default_layout: Any = layout_input.get(DI2008AllAnalogChannels, DI2008AnalogLayout.IGNORE)

        channel: DI2008AnalogChannels
        for channel in DI2008AnalogChannels:
            layout = layout_input.get(channel, default_layout)
            assert layout is not None
            if layout is not DI2008AnalogLayout.IGNORE:
                ports.append(self.get_di2008_port_layout(channel, layout))

        return ports

    def get_di2008_port_layout(
        self,
        channel: DI2008AnalogChannels,
        layout: DI2008AnalogLayout
        | tuple[DI2008AnalogLayout, DI2008TCType | DI2008ADCRange],
    ) -> _DI2008Port:
        """
        Given some layout and the channel, determine which device is connected, get the correct rescaling factor, and return the port
        """
        connected_type: DI2008AnalogLayout
        rescalar: Callable[[int], float]
        final_layout: int

        # The TC and ADC needs 2 values, so it's a 2-tuple. The IGNORE version is not
        if isinstance(layout, tuple):
            if len(layout) != 2:
                raise Exception("DI-2008 Layout must be 1 enum or tuple of 2!")
            connected_type = layout[0]
        else:
            connected_type = layout

        # For Thermocouple, get the right rescalar and set the layout
        if connected_type is DI2008AnalogLayout.TC:
            assert isinstance(layout, tuple)
            assert isinstance(layout[1], DI2008TCType)
            tc_type: DI2008TCType = layout[1]
            final_layout = (DI2008AnalogLayout.TC | tc_type) | channel
            rescalar = self.tc_rescalars[tc_type]

        # For ADC, use the acual value to rescale it
        elif connected_type is DI2008AnalogLayout.ADC:
            assert isinstance(layout, tuple)
            assert isinstance(layout[1], DI2008ADCRange)
            adc_range: DI2008ADCRange = layout[1]
            final_layout = adc_range.value[0] | channel
            rescalar = lambda x: adc_range.value[1] * (x / 32768.0)

        else:
            raise Exception("Not a valid layout!")

        return _DI2008Port(channel, final_layout, connected_type, rescalar)

    def read_di2008(self) -> dict[DI2008AnalogChannels, float | int]:
        """
        Read from each configured port on this DI-2008 and rescale based on the configuration. Return a dictionary of channels to values.
        """
        res: dict[DI2008AnalogChannels, float | int] = {}
        assert self.scw is not None
        assert self.scw.ports is not None
        num_ports = len(self.scw.ports)
        while self.scw.conn.in_waiting < (2 * num_ports):
            pass
        raw_bytes: bytes = bytes(self.scw.conn.read(2 * num_ports))
        # Attemping to flush regularly to stop the stop 01 error.
        self.scw.conn.flush()

        i: int
        port: _DI2008Port
        for i, port in enumerate(self.scw.ports):
            these_two_bytes: bytes = raw_bytes[2 * i : 2 * (i + 1)]

            formatted_byte: int
            # Ignore ports marked as such
            if port.connected_type is DI2008AnalogLayout.IGNORE:
                continue

            # All other types
            else:
                formatted_byte = int.from_bytes(
                    these_two_bytes, byteorder="little", signed=True
                )

            # Rescale as necessary
            final: float = port.rescalar(formatted_byte)
            assert isinstance(port.channel, DI2008AnalogChannels)
            res[port.channel] = final

        return res

    def _tc_j(self, x: int) -> float:
        """Rescalar for J-Type Thermocouple"""
        return (0.021515 * x) + 495.0

    def _tc_k(self, x: int) -> float:
        """Rescalar for K-Type Thermocouple"""
        return (0.023987 * x) + 586.0

    def _tc_t(self, x: int) -> float:
        """Rescalar for T-Type Thermocouple"""
        return (0.009155 * x) + 100.0

    def _tc_b(self, x: int) -> float:
        """Rescalar for B-Type Thermocouple"""
        return (0.023956 * x) + 1035.0

    def _tc_r_s(self, x: int) -> float:
        """Rescalar for R-Type and S-Type Thermocouple"""
        return (0.02774 * x) + 859.0

    def _tc_e(self, x: int) -> float:
        """Rescalar for E-Type Thermocouple"""
        return (0.018311 * x) + 400.0

    def _tc_n(self, x: int) -> float:
        """Rescalar for N-Type Thermocouple"""
        return (0.022888 * x) + 550.0


class DI2008:
    """
    Container for multiple DI-2008 Interface objects
    Designed to manage automatic synchronization and parametrization.
    """

    def __init__(
        self,
        global_layout_dict: dict[Any, Any],
    ):
        """
        Signature for DI2008
        global_layout_dict: Dictionary of input parameters. See README for more details.
        """
        # Does NOT currently support any config files. Gonna have to work on that!!!
        global_config: dict[Any, Any]
        individual_layout_dicts: dict[int, Any] | None
        target_sns: list[int] = []
        target_sns += global_layout_dict.get(DI2008SerialNums, [])

        k: str
        keys_to_remove: list[str] = []
        for k in global_layout_dict.keys():
            try:
                target_sns.append(self._get_int_from_str(k))
                keys_to_remove.append(k)
            except (ValueError, TypeError):
                pass

        assert len(target_sns) > 0
        ik: int
        ktr: str
        individual_layout_dicts = {}
        for ik, ktr in zip(target_sns, keys_to_remove):
            individual_layout_dicts[ik] = global_layout_dict.pop(ktr)

        global_config = global_layout_dict

        self.di2008s: list[_DI2008Instance] = []
        sn: int
        for sn in target_sns:
            self.di2008s.append(
                _DI2008Instance(
                    sn, individual_layout_dicts.get(sn), global_config=global_config
                )
            )

    def start_di2008s(self) -> None:
        """Perform the synchronized start for the DI-2008s. See the DI-2008 Protocl for details"""

        di2008: _DI2008Instance
        if len(self.di2008s) > 1:
            # Synchronized Start
            # As taken from the docs (top of page 5)
            syncget_0_vals: list[int] = []
            for di2008 in self.di2008s:
                syncget_0_resp: str | None = di2008.scw.echo("syncget 0")
                assert syncget_0_resp is not None
                syncget_0: str | int = syncget_0_resp.split(" ")[-1]
                syncget_0 = int(syncget_0)
                syncget_0_vals.append(syncget_0)

            syncget_0_c: int = sum(syncget_0_vals) // len(syncget_0_vals)
            syncget_3_vals: list[int] = []
            for di2008 in self.di2008s:
                syncget_3_resp: str | None = di2008.scw.echo("syncget 3")
                assert syncget_3_resp is not None
                syncget_3: str | int = syncget_3_resp.split(" ")[-1]
                syncget_3 = int(syncget_3)
                syncget_3_vals.append(syncget_3)

            s3v0: int = syncget_3_vals[0]
            if any(s != s3v0 for s in syncget_3_vals) or s3v0 != syncget_0_c:
                for di2008 in self.di2008s:
                    di2008.scw.send_command(f"syncset {syncget_0_c}")

                time.sleep(1.0)

            syncget_f_resp: str | None = self.di2008s[0].scw.echo("syncget 2")
            assert syncget_f_resp is not None
            syncget_f: int | str = syncget_f_resp.split(" ")[-1]
            syncget_f = int(syncget_f)
            syncget_g: int = syncget_f ^ 0x0400
            if syncget_g == 0:
                syncget_g = 1

            for di2008 in self.di2008s:
                di2008.scw.send_command(f"syncstart {syncget_g}")

        else:
            for di2008 in self.di2008s:
                di2008.start()

    def read_di2008s(self) -> dict[int, dict[DI2008AnalogChannels, float | int]]:
        """
        For each connected DI2008, read all configured channels of each and return a dictionary mapping serial numbers to dictionaries of channels to values
        """
        res: dict[int, dict[DI2008AnalogChannels, float | int]] = {}
        di2008: _DI2008Instance
        for di2008 in self.di2008s:
            res[di2008.serial_num] = di2008.read_di2008()

        return res

    @staticmethod
    def _get_int_from_str(val: str) -> int:
        """
        Parse a decimal or hexadecimal string into an integer
        """
        try:
            return int(val)
        except (ValueError, TypeError):
            return int(val, base=16)
