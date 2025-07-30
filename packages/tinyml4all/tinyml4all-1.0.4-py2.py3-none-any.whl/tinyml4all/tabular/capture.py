import csv
import os.path
from typing import List, Any, Dict, Callable

from tinyml4all.support import assert_folder, ask_empty, countdown
from tinyml4all.support.capture.Progress import Progress
from tinyml4all.support.capture.SerialReader import SerialReader
from tinyml4all.support.types import as_list_of_strings, coalesce
from tinyml4all.support.userwarn import userwarn


def capture_serial(
    port: str,
    save_to: str,
    baudrate: int = 115200,
    num_samples: int = 0,
    duration: str = "",
    headings: str | List[str] = None,
    append_values: List[Any] = None,
    transform: Dict[str, Callable[[str], str]] = None,
):
    """
    Capture tabular data from a serial port
    :param port: serial port of the device (e.g. COM1, /dev/ttyACM0, etc.)
    :param save_to: destination file
    :param baudrate: must match with the Arduino sketch
    :param num_samples: how many samples to capture
    :param duration: how long to capture
    :param headings: CSV column names
    :param append_values: append custom values to each row
    :param transform: transform values before writing to file
    :return:
    """
    assert_folder(os.path.abspath(os.path.dirname(save_to)))
    ask_empty(save_to)

    headings = as_list_of_strings(headings)
    append_values = coalesce(append_values, [])

    # prepend headings if file is empty
    if len(headings) > 0 and os.path.getsize(save_to) == 0:
        with open(save_to, "w") as f:
            csv.writer(f).writerow(headings)

    # assert we can open the serial port
    with SerialReader(port=port, baudrate=baudrate):
        pass

    # open serial and read lines
    countdown()

    with SerialReader(port=port, baudrate=baudrate) as reader:
        with Progress(count=num_samples, duration=duration) as progress:
            with open(save_to, "a") as output:
                writer = csv.writer(output)

                while not progress.expired():
                    if (line := reader.readline()) is None:
                        continue

                    values = next(csv.reader([line]))

                    if len(append_values) > 0:
                        values += append_values

                    # assert values are consistent with headings
                    if 0 < len(headings) != len(values):
                        userwarn(
                            f"Inconsistent number of values ({len(values)}). {len(headings)} expected based on headings"
                        )
                        continue

                    # transform values
                    if transform is not None:
                        kv = {
                            heading: transform.get(heading, lambda x: x)(value)
                            for heading, value in zip(headings, values)
                        }
                        values = [kv[heading] for heading in headings]

                    writer.writerow(values)
                    progress.increment()
