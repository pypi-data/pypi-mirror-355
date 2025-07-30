import os.path
from typing import List, Generator, Tuple

from tinyml4all.audio.Album import Album
from tinyml4all.audio.WAV import WAV
from tinyml4all.audio.classification.OverlapPlot import OverlapPlot
from tinyml4all.audio.classification.SequentialPlot import SequentialPlot


class ClassificationAlbum(Album):
    """
    Album of classification tasks
    """

    @property
    def labels(self) -> List[str]:
        """
        Get list of file labels
        :return:
        """
        return [file.dirname for file in self.files]

    @property
    def unique_labels(self) -> List[str]:
        """
        Get list of unique labels
        :return:
        """
        return sorted(list(set(self.labels)))

    @property
    def num_labels(self) -> int:
        """
        Get number of unique labels
        :return:
        """
        return len(self.unique_labels)

    @property
    def overlap_plot(self) -> OverlapPlot:
        """
        Get instance of overlap plotter
        :return:
        """
        return OverlapPlot(self)

    @property
    def sequential_plot(self) -> SequentialPlot:
        """
        Get instance of sequential plotter
        :return:
        """
        return SequentialPlot(self)

    @property
    def groups(self) -> Generator[Tuple[str, List[WAV]], None, None]:
        """
        Group by label
        :return:
        """
        for label in self.unique_labels:
            yield (
                label,
                [file for l, file in zip(self.labels, self.files) if l == label],
            )
