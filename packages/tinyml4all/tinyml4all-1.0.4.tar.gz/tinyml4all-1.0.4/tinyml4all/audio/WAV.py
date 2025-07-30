import os.path
from typing import Self

import numpy as np
from durations import Duration
from scipy.io import wavfile
from librosa import resample


class WAV:
    """
    WAV Audio file
    """

    def __init__(self, path: str, data: np.ndarray = None, rate: int = None):
        """
        Constructor
        :param path:
        :param data: allow to create WAV from data
        :param rate: allow to create WAV from data
        """
        if data is None:
            assert os.path.isfile(path), f"File {path} not found"
            rate, data = wavfile.read(path)

        assert rate is not None, "You must set a sampling rate"

        # rescale int16 to [-1, 1]
        if np.abs(data).max() > 1:
            data = np.interp(data.astype(float), [-32768, 32767], [-1, 1])

        self.path = path
        self.data = data
        self.rate = rate

    def __len__(self) -> int:
        """
        Get length of data
        :return:
        """
        return len(self.data)

    def __repr__(self):
        """
        Get human representation
        :return:
        """
        return f"WAV(filename={self.path}, rate={self.rate}, len={len(self)})"

    @property
    def dirname(self) -> str:
        """
        Get directory name
        :return:
        """
        return os.path.basename(os.path.dirname(self.path))

    def matches(self, other: Self) -> bool:
        """
        Test if two WAVs share the same length and sample rate
        :param other:
        :return:
        """
        return self.rate == other.rate and len(self) == len(other)

    def resample(self, freq: int) -> Self:
        """
        Alter sampling frequency
        :param freq:
        :return:
        """
        if freq == self.rate:
            return self

        self.data = resample(y=self.data, orig_sr=self.rate, target_sr=freq)
        self.rate = freq

        return self

    def trim(self, duration: str = None, target_len: int = None) -> "WAV":
        """
        Trim audio to given duration
        :param duration:
        :param target_len:
        :return:
        """
        assert duration is not None or target_len is not None, (
            "You must set either duration or target_len"
        )

        if target_len is None:
            millis = Duration(duration).to_miliseconds()
            target_len = int(millis * self.rate / 1000)

        self.data = self.data[:target_len]

        return self

    def write(self, filename: str = None) -> Self:
        """
        Write to disk
        :param filename:
        :return:
        """
        wavfile.write(filename or self.path, rate=self.rate, data=self.data)

        return self
