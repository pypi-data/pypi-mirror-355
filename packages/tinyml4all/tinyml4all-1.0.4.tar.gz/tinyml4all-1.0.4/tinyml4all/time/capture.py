from datetime import datetime, timedelta
from typing import List, Any

from tinyml4all.support import userwarn
from tinyml4all.tabular.capture import capture_serial as capture_serial_tabular


def capture_serial(
    port: str,
    save_to: str,
    baudrate: int = 115200,
    num_samples: int = 0,
    duration: str = "",
    headings: str | List[str] = None,
    append_values: List[Any] = None,
):
    """
    Capture time data from a serial port
    :param port: serial port of the device (e.g. COM1, /dev/ttyACM0, etc.)
    :param save_to: destination file
    :param baudrate: must match with the Arduino sketch
    :param num_samples: how many samples to capture
    :param duration: how long to capture
    :param headings: CSV column names
    :param append_values: append custom values to each row
    :return:
    """
    started_at = datetime.now()

    if "millis" not in headings:
        userwarn(
            "No 'millis' column is provided. Will use time of line reception instead, even if not recommended."
        )

    def millis_to_timestamp(millis: str) -> str:
        return str(started_at + timedelta(milliseconds=int(millis)))

    return capture_serial_tabular(
        port=port,
        save_to=save_to,
        baudrate=baudrate,
        num_samples=num_samples,
        duration=duration,
        headings=headings,
        append_values=append_values,
        transform={"millis": millis_to_timestamp},
    )
