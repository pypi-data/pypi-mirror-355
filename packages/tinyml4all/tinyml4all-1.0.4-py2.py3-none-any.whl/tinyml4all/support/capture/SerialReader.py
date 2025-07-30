import re
from typing import Union

from serial import Serial, SerialException
from serial.tools import list_ports


class SerialReader:
    """
    Reads data from a serial port
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: int = 1):
        """
        Constructor
        :param port:
        :param baudrate:
        :param timeout:
        """
        self.port = self.resolve_port(port)
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.bytes = bytes([])
        self.error = None

    def __enter__(self):
        """
        Open serial port
        :return:
        """
        try:
            self.serial = Serial(self.port, self.baudrate, timeout=self.timeout)
            self.flush()
            print(f"Connected to serial port {self.port}")

            return self
        except SerialException as e:
            # provide hint to close the Arduino Serial Monitor
            if "resource busy" in str(e):
                raise RuntimeError(
                    f"{self.port} port is busy. Maybe you have the Arduino Serial Monitor open?"
                )

            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close serial port
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self.serial:
            self.serial.close()

        print("Disconnected from serial port")

    def readline(self) -> Union[str | None]:
        """
        Read line
        :return:
        """
        try:
            if (line := self.serial.readline().decode("utf-8").strip()) != "":
                return line
        except SerialException:
            pass

        return None

    def read(self, size: int) -> bytes:
        """
        Read binary data
        :param size:
        :return:
        """
        return self.serial.read(size)

    def delimited(self, start: bytes, end: bytes) -> bytes | None:
        """
        Find data between delimiters
        :param start:
        :param end:
        :return:
        """
        self.bytes += self.read(256)

        try:
            # find the rightmost occurrence of the delimited data
            eof = self.bytes.rindex(end)
            sof = self.bytes.rindex(start, 0, eof - 1)
            data = self.bytes[sof + len(start) : eof]
            self.bytes = self.bytes[eof + len(end) :]

            return data
        except ValueError:
            return None

    def writeline(self, line: str):
        """
        Write line
        :param line:
        :return:
        """
        self.serial.write(line.encode("utf-8") + b"\r\n")

    def flush(self):
        """
        Flush serial port
        :return:
        """
        self.serial.reset_input_buffer()
        self.bytes = bytes([])

    def resolve_port(self, port: str) -> str:
        """
        Allow partial match for port using the * character
        :param port:
        :return:
        """
        if "*" not in port:
            return port

        pattern = re.compile(port.replace("*", ".+"), re.IGNORECASE)

        for entry in list_ports.comports():
            if (
                pattern.search(entry.name) is not None
                or pattern.search(entry.device) is not None
            ):
                return entry.device

        raise ValueError(f"Cannot find serial port {port}")
