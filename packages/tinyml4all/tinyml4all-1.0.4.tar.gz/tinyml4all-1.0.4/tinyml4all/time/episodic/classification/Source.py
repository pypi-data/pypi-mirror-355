from bisect import bisect_left
from typing import Generator, Tuple

import pandas as pd

from tinyml4all.time.Source import Source as Base


class Source(Base):
    """
    Source for episodic classification time series
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.heights = {}

    @property
    def events(self) -> Generator[Tuple[str, pd.Timestamp], None, None]:
        """
        Iterate over groups of labels
        :return:
        """
        for i, label in enumerate(self.Y_true):
            if label is not None:
                yield label, self.T[i], self.heights.get(str(self.T[i]), None)

    def add_label(self, label: str, t: str, height: float = None):
        """
        Add label to point
        :param label:
        :param t:
        :param height:
        :return:
        """
        t = pd.Timestamp(t)

        if t < self.start_at or t > self.end_at:
            return

        index = bisect_left(self.T, t)
        t = self.T[index]
        self.Y_true[index] = label
        self.heights[str(t)] = height
