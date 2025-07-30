import os
from typing import Generator, Tuple, Iterable

import numpy as np
import pandas as pd
from pandas import DataFrame

from tinyml4all.support import infer_timestamp_column, Array, plain_filename
from tinyml4all.support.types import coalesce


class Source:
    """
    Source of time series
    """

    @classmethod
    def read_csv(cls, path: str, index: int, **kwargs) -> "Source":
        """
        Read CSV file
        :param path:
        :param index:
        :return:
        """
        return cls(source_name=path, index=index, data=pd.read_csv(path, **kwargs))

    def __init__(
        self,
        source_name: str,
        index: int,
        data: DataFrame,
        Y_true: Array = None,
        Y_pred: Array = None,
        T: Array = None,
    ):
        """
        Constructor
        :param source_name:
        :param index:
        :param data:
        """
        if T is None:
            t_column = infer_timestamp_column(data)
            T = data[t_column]
            data = data.drop(columns=t_column)

        self.source_name = source_name
        self.index = index
        self.df: DataFrame = data
        self.T = np.asarray([pd.Timestamp(t) for t in T])
        self.Y_true: list[str | None] = coalesce(Y_true, lambda: [None] * len(self))
        self.Y_pred: list[str | None] = coalesce(Y_pred, lambda: [None] * len(self))

    def __len__(self) -> int:
        """
        Get number of rows
        :return:
        """
        return len(self.df)

    def __repr__(self):
        """
        Get string representation
        :return:
        """
        return f"Source(source_name={self.source_name}, len={len(self)})"

    def __getattr__(self, item):
        """
        Proxy to DataFrame
        :param item:
        :return:
        """
        if item in self.__dict__:
            return self.__dict__.get(item)

        if item == "df":
            return None

        return getattr(self.df, item)

    @property
    def basename(self) -> str:
        """
        Get basename
        :return:
        """
        return os.path.basename(self.source_name)

    @property
    def start_at(self) -> pd.Timestamp:
        """
        Get start timestamp
        :return:
        """
        return pd.Timestamp(self.T[0])

    @property
    def end_at(self) -> pd.Timestamp:
        """
        Get end timestamp
        :return:
        """
        return pd.Timestamp(self.T[-1])

    def assert_non_overlapping(self, other: "Source"):
        """
        Assert that there are no overlapping timestamps
        :return:
        """
        a1 = np.min(self.T)
        a2 = np.max(self.T)
        b1 = np.min(other.T)
        b2 = np.max(other.T)

        assert a2 < b1 or b2 < a1, (
            f"Overlapping timestamps: [{a1} - {a2}] and [{b1} - {b2}]"
        )

    def update(
        self,
        source_name: str = None,
        index: int = None,
        data: DataFrame = None,
        df: DataFrame = None,
        T: Array = None,
        Y_true: Array = None,
        Y_pred: Array = None,
        input_mask: np.ndarray[bool] = None,
        **kwargs,
    ) -> "Source":
        """
        Update and return new
        :param source_name:
        :param data:
        :param index:
        :param T:
        :param Y_true:
        :param Y_pred:
        :param input_mask:
        :return:
        """
        data = coalesce(data, df)
        data = coalesce(data, lambda: self.df.copy())
        input_mask = coalesce(input_mask, lambda: np.ones(len(data), dtype=bool))

        return type(self)(
            source_name=coalesce(source_name, self.source_name),
            index=coalesce(index, self.index),
            data=coalesce(data, lambda: self.df.copy()).iloc[input_mask],
            T=coalesce(T, self.T)[input_mask],
            Y_true=np.asarray(coalesce(Y_true, lambda: self.Y_true.copy()))[
                input_mask
            ].tolist(),
            Y_pred=coalesce(Y_pred, lambda: self.Y_pred.copy()),
        )
