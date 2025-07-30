import os
import tempfile
from io import BytesIO

from PIL import Image

from tinyml4all.support import assert_folder
from tinyml4all.support.capture.Progress import Progress
from tinyml4all.support.capture.SerialReader import SerialReader
from tinyml4all.image.HTTPD import httpd_start


def capture_serial(
    port: str,
    save_to: str,
    num_samples: int,
    baudrate: int = 115_200 * 2,
):
    """
    Capture jpeg images from Serial
    :param port:
    :param save_to:
    :param num_samples:
    :param baudrate:
    :return:
    """
    assert_folder(os.path.abspath(save_to))

    with tempfile.TemporaryDirectory("wb+") as tmpdir:
        tmpfile = os.path.join(tmpdir, "frame.jpg")

        with SerialReader(port=port, baudrate=baudrate) as reader:
            with Progress(count=num_samples) as progress:
                # display stream preview in the browser
                # (works across OSes)
                httpd = httpd_start(
                    save_to, tmpfile, on_capture=lambda *args: progress.increment()
                )

                while not progress.expired():
                    if (data := reader.delimited(b"#SOF#", b"#EOF#")) is None:
                        if select_model(reader.bytes, reader):
                            continue

                    if data[0] == 0xFF and data[1] == 0xD8:
                        # looks like a valid jpeg image
                        image = Image.open(BytesIO(data))
                        # make image available to http server
                        image.save(tmpfile)

                httpd.shutdown()


def select_model(data: bytes, reader: SerialReader) -> bool:
    """
    Select camera model
    :return:
    """
    # check if user forgot to select a model
    if b"Select camera model" in data:
        model_ix = input(
            "Select camera model:\n [1] AiThinker\n [2] XIAO\n [3] M5\n [4] M5 Fish Eye\n [5] M5 Timer X\n [6] ESP-EYE\n [7] ESP-EYE S3\n [8] WROVER\n [9] WROOM S3\n [10] TTGO PLUS\n [11] TTGO PIR\nEnter choice number [1-11]: "
        ).strip()
        reader.writeline(model_ix)
        reader.flush()

        return True

    return False
