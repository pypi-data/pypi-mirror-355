from typing import List

import numpy as np
import pandas as pd
from pandas import Timedelta, Timestamp

from tinyml4all.support import numeric, get_frequency
from tinyml4all.support.types import coalesce, cast
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock
from tinyml4all.tabular.classification.ClassificationTable import ClassificationTable
from tinyml4all.time.continuous.classification.ClassificationTimeTable import (
    ClassificationTimeTable,
)


class Window(ProcessingBlock):
    """
    Extract features from windows of data
    """

    def __init__(
        self,
        length: str | pd.Timedelta,
        shift: str | pd.Timedelta | None,
        features: List[callable],
    ):
        """
        Constructor
        :param length:
        :param shift:
        """
        super().__init__()

        self.length = cast(length, pd.Timedelta)
        self.shift = cast(shift, pd.Timedelta) if shift is not None else self.length / 2
        self.features = features
        self.length_count = None
        self.shift_count = None

    def __str__(self) -> str:
        """
        Get string representation
        :return:
        """
        return f"Window(length={self.length.total_seconds()}s, shift={self.shift.total_seconds()}s, features={self.features})"

    def fit(self, dataset, *args, **kwargs):
        """
        Fit
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        # nothing to fit
        self.remember_working_variables(numeric(dataset.df))

    def transform(self, dataset, *args, **kwargs):
        """
        Transform
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        labels = None
        windows = None
        timestamps = []
        t0 = Timestamp(dataset.T[0])
        freq = get_frequency(dataset.T)

        self.length_count = int(self.length.total_seconds() * freq)
        # warning: we *could* add a check to set shift_count at least to 1
        # (because 0 will throw an error later)
        # but we're keeping it as is as a signal of bad windowing sizing
        self.shift_count = int(self.shift.total_seconds() * freq)

        # build windows
        for source, label, start_at, end_at, df in dataset.groups:
            dt = start_at - t0

            if label is not None:
                if len(df) < self.length_count:
                    continue

                indices = np.lib.stride_tricks.sliding_window_view(
                    np.arange(len(df)), self.length_count
                )[:: self.shift_count]
                middle_indices = indices[:, indices.shape[1] // 2]
                data = df.to_numpy()[indices]
                timestamps += [t + dt for t in dataset.T[middle_indices]]

                if windows is None:
                    windows = data
                    labels = [label] * len(data)
                else:
                    windows = np.vstack((windows, data))
                    labels.extend([label] * len(data))

        assert "df" in locals().keys(), "No valid labels found"

        # extract features
        def extract_features(data: np.ndarray[float]) -> List[float]:
            return [f for extractor in self.features for f in extractor(data)]

        X = np.asarray([extract_features(w) for w in windows])
        feature_names = [
            name
            for extractor in self.features
            for name in extractor.get_feature_names(df.columns)
        ]

        return {
            "type": ClassificationTimeTable,
            "df": pd.DataFrame(X, columns=feature_names),
            "Y_true": labels,
            "T": timestamps,
        }
