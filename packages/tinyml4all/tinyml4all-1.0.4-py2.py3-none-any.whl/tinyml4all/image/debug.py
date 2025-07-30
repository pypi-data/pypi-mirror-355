import os
import re
import struct
import tempfile
from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw

from tinyml4all.image.capture import select_model
from tinyml4all.support import assert_folder, userwarn
from tinyml4all.support.capture.Progress import Progress
from tinyml4all.support.capture.SerialReader import SerialReader
from tinyml4all.image.HTTPD import httpd_start


def debug_serial(
    port: str,
    baudrate: int = 115_200 * 2,
):
    """
    Debug object detection results from Serial
    :param port:
    :param baudrate:
    :return:
    """
    with tempfile.TemporaryDirectory("wb+") as tmpdir:
        tmpfile = os.path.join(tmpdir, "frame.jpg")

        with SerialReader(port=port, baudrate=baudrate) as reader:
            # display stream preview in the browser
            # (works across OSes)
            data = bytes([])
            sof_marker = b"#SOF#"
            eof_marker = b"#EOF#"
            bbox_sof_marker = b"Found "
            bbox_eof_marker = sof_marker
            frame = None
            palette = ["#36a2eb", "#ff6384", "#ff9f40", "#4bc0c0", "#9966ff", "#ffcd56"]
            colormap = {}

            httpd_start(save_to="", tmpfile=tmpfile)

            while True:
                data += reader.read(256)

                if select_model(data, reader):
                    data = bytes([])
                    continue

                # look for frame
                try:
                    # find the rightmost occurrence of the delimited data
                    eof = data.rindex(eof_marker)
                    sof = data.rindex(sof_marker, 0, eof - 1)
                    frame = data[sof + len(sof_marker) : eof]
                    print(f"len(frame)={len(frame)}")
                    data = data[eof + len(eof_marker) :]
                except ValueError:
                    pass

                # look for bounding boxes
                try:
                    # find the rightmost occurrence of the delimited data
                    eof = data.rindex(bbox_eof_marker)
                    sof = data.rindex(bbox_sof_marker, 0, eof - 1)
                    bboxes = data[sof + len(bbox_sof_marker) : eof].decode("utf-8")
                    data = data[eof:]

                    bboxes = decode_bboxes(bboxes)
                    print(f"bboxes={bboxes}")
                except ValueError:
                    pass

                # if valid frame, display it
                if frame is not None:
                    # frame may be grayscale or RGB565, either 96x96 or 160x120
                    if len(frame) == 96 * 96:
                        image = decode_gray(frame, 96, 96)
                    if len(frame) == 160 * 120:
                        image = decode_gray(frame, 160, 120)
                    elif len(frame) == 96 * 96 * 2:
                        image = decode_rgb(frame, 96, 96)
                    elif len(frame) == 160 * 120 * 2:
                        image = decode_rgb(frame, 160, 120)
                    else:
                        userwarn(f"Unknown frame length ({len(frame)}")

                    # make image available to http server
                    # scale up to 2x for better display
                    image = image.resize((image.width * 2, image.height * 2))

                    # draw bboxes centroids
                    if len(bboxes):
                        draw = ImageDraw.Draw(image)

                        for bbox in bboxes:
                            radius = 8
                            label = bbox["label"]
                            cx = bbox["cx"] * 2
                            cy = bbox["cy"] * 2

                            if label not in colormap:
                                colormap[label] = palette.pop(0)

                            draw.ellipse(
                                xy=(cx - radius, cy - radius, cx + radius, cy + radius),
                                outline=colormap[label],
                                width=radius,
                            )

                    image.save(tmpfile)


def decode_gray(data: bytes, w: int, h: int) -> Image:
    """
    Decode grayscale data
    :param data:
    :param w:
    :param h:
    :return:
    """
    return Image.fromarray(
        np.asarray([int(x) for x in data], dtype=np.uint8).reshape((h, w))
    )


def decode_rgb(data: bytes, w: int, h: int) -> Image:
    """
    Decode RGB565 data
    :param data:
    :param w:
    :param h:
    :return:
    """
    u16 = list(struct.unpack(f">{'H' * (len(data) // 2)}", data))
    r = [255 / 31 * ((p >> 11) & 0x1F) for p in u16]
    g = [255 / 63 * ((p >> 5) & 0x3F) for p in u16]
    b = [255 / 31 * (p & 0x1F) for p in u16]

    return Image.fromarray(
        np.dstack([np.asarray(ch).reshape((h, w)) for ch in [r, g, b]]).astype(np.uint8)
    )


def decode_bboxes(data: str) -> list[dict]:
    """
    Decode bounding boxes
    :param data:
    :return:
    """
    lines = [line.strip() for line in data.split(" > ")[1:]]
    matches = [
        re.match(r"^(.+?) at coordinates (\d+), (\d+) \(confidence (\d+\.\d+)\)$", line)
        for line in lines
    ]
    groups = [match.groups() for match in matches if match is not None]

    return [
        {"label": label, "cx": int(cx), "cy": int(cy), "confidence": float(confidence)}
        for label, cx, cy, confidence in groups
    ]
