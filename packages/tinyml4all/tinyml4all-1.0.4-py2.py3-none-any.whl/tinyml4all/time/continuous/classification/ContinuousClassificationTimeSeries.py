from typing import List, Self, Generator, Tuple

import numpy as np
import pandas as pd
from scipy.stats import mode

from tinyml4all.support import non_null, numeric, get_frequency
from tinyml4all.support.traits.HasClassmap import HasClassmap
from tinyml4all.support.types import coalesce, cast
from tinyml4all.time.TimeSeries import TimeSeries
from tinyml4all.time.continuous.Line import Line
from tinyml4all.time.continuous.classification.LabelGUI import LabelGUI
from tinyml4all.time.continuous.classification.Source import Source


class ContinuousClassificationTimeSeries(TimeSeries, HasClassmap):
    """
    Time series for continuous classification
    """

    @classmethod
    def get_source_class(cls) -> type[Self]:
        """
        Get source class
        :return:
        """
        return Source

    @property
    def line(self) -> Line:
        """
        Get line plotter
        :return:
        """
        return Line(self)

    @property
    def label_gui(self) -> LabelGUI:
        """
        Get label UI
        :return:
        """
        return LabelGUI(self)

    @property
    def groups(
        self,
    ) -> Generator[
        Tuple[Source, str, pd.Timestamp, pd.Timestamp, pd.DataFrame], None, None
    ]:
        """
        Iterate over groups of labels
        :return:
        """
        for source in self.sources:
            for label, start_at, end_at, df in source.groups:
                yield source, label, start_at, end_at, df

    def label_from_source(self):
        """
        Typo
        :return:
        """
        return self.label_from_sources()

    def add_label(self, label: str, start_at: str, end_at: str):
        """
        Add label
        :param label:
        :param start_at:
        :param end_at:
        :return:
        """
        [source.add_label(label, start_at, end_at) for source in self.sources]

    def as_windows(
        self, duration: str, shift: str = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Split time series into windows
        :param duration:
        :param shift:
        :return:
        """
        duration = cast(duration, pd.Timedelta)
        shift = cast(coalesce(shift, duration), pd.Timedelta)
        freq = get_frequency(self.T)
        window_len = int(freq * duration.total_seconds())
        shift_len = int(freq * shift.total_seconds())
        window_indices = np.lib.stride_tricks.sliding_window_view(
            np.arange(len(self.df)), window_len
        )[::shift_len]
        X = numeric(self.df).to_numpy()
        classmap = self.classmap
        Y = np.asarray([classmap.get(y) for y in self.Y_true])

        return np.asarray([X[idx] for idx in window_indices]), np.asarray(
            [mode(Y[idx]).mode for idx in window_indices]
        ).astype(int)
