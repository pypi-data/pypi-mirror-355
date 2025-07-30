import csv
import os.path
from typing import List

from tinyml4all.support import assert_folder, ask_empty, countdown
from tinyml4all.support.capture.SerialReader import SerialReader
from tinyml4all.support.types import as_list_of_strings


def prepare_serial_capture(
    port: str, baudrate: int, save_to: str, headings: str | List[str] = None
) -> List[str]:
    """
    Preliminary operations for serial capture
    :param port:
    :param baudrate:
    :param save_to:
    :param headings:
    :return: the list of headings
    """
    assert_folder(os.path.abspath(os.path.dirname(save_to)))
    ask_empty(save_to)

    headings = as_list_of_strings(headings)

    # prepend headings if file is empty
    if len(headings) > 0 and os.path.getsize(save_to) == 0:
        with open(save_to, "w") as f:
            csv.writer(f).writerow(headings)

    # assert we can open the serial port
    with SerialReader(port=port, baudrate=baudrate):
        pass

    # open serial and read lines
    countdown()

    return headings
