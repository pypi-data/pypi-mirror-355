import os.path
import warnings
from glob import glob
from pathlib import Path

from tinyml4all.audio.WAV import WAV
from tinyml4all.audio.classification.OverlapPlot import OverlapPlot
from tinyml4all.support import warn_or_raise, userwarn


class Album:
    """
    Base class to handle audio files
    """

    @classmethod
    def read_wav_folders(cls, *folders, ignore_errors: bool = True):
        """
        Reads all the wav files in the folders and returns an Album object
        :param folders: list of folders
        :param ignore_errors: ignore errors when reading wav files
        :return: Album object
        """
        files = []

        for folder in folders:
            for filename in sorted(glob(os.path.join(folder, "*.wav"))):
                files.append(WAV(filename))

                # assert all samples have the same duration and sample rate
                if not files[-1].matches(files[0]):
                    userwarn(
                        f"File {files[-1].path} does not match length and sample rate of {files[0]}. Will try resample and trim."
                    )
                    files[-1].resample(files[0].rate).trim(target_len=len(files[0]))

                if not files[-1].matches(files[0]):
                    warn_or_raise("Can't align files", warn=ignore_errors)

        return cls(files=files)

    def __init__(self, files: list[WAV]):
        """
        Constructor
        :param files:
        """
        self.files = sorted(files, key=lambda file: file.dirname)

    def __len__(self) -> int:
        """
        Get length of album
        :return:
        """
        return len(self.files)

    def __repr__(self):
        """
        Get human representation
        :return:
        """
        return f"Album(files={len(self)})"

    @property
    def overlap_plot(self) -> OverlapPlot:
        """
        Get instance of overlap plotter
        :return:
        """
        return OverlapPlot(self)
