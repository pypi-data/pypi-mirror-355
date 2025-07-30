import os.path
import re
from struct import unpack
from time import time

import numpy as np
import pandas as pd
from scipy.io import wavfile
from ulid import ULID

from tinyml4all.audio.support import parse_freq
from tinyml4all.support import assert_folder, warn_non_empty, cast
from tinyml4all.support.capture.Progress import Progress
from tinyml4all.support.capture.SerialReader import SerialReader


def capture_serial(
    port: str,
    num_samples: int,
    save_to: str,
    word_duration: str,
    mic_frequency: str,
    baudrate: int = 115_200 * 2,
    chunk_size: int = 256,
):
    """
    Capture audio data from a serial port
    :param port:
    :param save_to:
    :param num_samples:
    :param word_duration: e.g. "2 seconds"
    :param mic_frequency: same as Arduino sketch (e.g. "16 khz")
    :param baudrate:
    :param chunk_size:
    :return:
    """
    assert_folder(os.path.abspath(save_to))
    warn_non_empty(save_to, "*.wav")

    word_duration = cast(word_duration, pd.Timedelta).total_seconds()
    mic_frequency = parse_freq(mic_frequency)
    sample_length = int(word_duration * mic_frequency * 2)
    # 100 ms of padding
    padding = int(mic_frequency * 0.1)
    captured = 0

    while captured < num_samples:
        if (
            input("Press [ENTER] to capture a sample or type 'stop' to exit: ")
            .lower()
            .strip()
            .startswith("s")
        ):
            break

        with SerialReader(port=port, baudrate=baudrate) as reader:
            sample = bytes([])
            started_at = time()

            while len(sample) < sample_length + padding:
                sample += reader.read(chunk_size)

            sample = sample[-sample_length:]
            num_values = len(sample) // 2
            audio = np.asarray(unpack(f"{num_values}h", bytes(sample)), dtype=np.int16)
            dest = f"{ULID()}.wav"
            wavfile.write(os.path.join(save_to, dest), mic_frequency, audio)
            print(f"Saved to {os.path.join(save_to, dest)}")
            print("it took", time() - started_at)
