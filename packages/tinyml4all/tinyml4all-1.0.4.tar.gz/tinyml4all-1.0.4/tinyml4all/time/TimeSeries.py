from itertools import combinations
from typing import List, Self

import numpy as np
import pandas as pd
from pandas import DataFrame

from tinyml4all.support.traits.HasSources import HasSources
from tinyml4all.support.traits.IsPickleable import IsPickleable
from tinyml4all.time.Source import Source


class TimeSeries(HasSources, IsPickleable):
    """
    Base class for time series
    """

    @classmethod
    def merge(cls, ts: "TimeSeries", update: dict) -> Self:
        """
        Merge time series with update
        :param ts:
        :param update:
        :return:
        """
        if len(ts.sources) > 1:
            ts = ts.collapse()

        ts.sources = [ts.sources[0].update(source_name=":memory:", index=0, **update)]

        return ts

    def __init__(self, sources: List[Source]):
        """
        Constructor
        :param sources:
        """
        HasSources.__init__(self, sources)

        # sort by start time
        self.sources = sorted(sources, key=lambda source: source.T[0])
        self.assert_non_overlapping()

    def __len__(self) -> int:
        """
        Get number of rows
        :return:
        """
        return sum(len(source) for source in self.sources)

    def __getattr__(self, item):
        """
        Proxy unknown attributes to pandas
        :param item:
        :return:
        """
        return getattr(self.df, item)

    def __repr__(self):
        """
        Get string representation
        :return:
        """
        return f"{self.__class__.__name__}(sources={self.sources})"

    @property
    def df(self) -> DataFrame:
        """
        Get data
        :return:
        """
        if len(self.sources) == 0:
            return pd.DataFrame()

        return pd.concat([source.df for source in self.sources])

    @property
    def T(self) -> np.ndarray:
        """
        Get timestamps
        :return:
        """
        if len(self.sources) == 0:
            return np.array([])

        return np.concatenate([source.T for source in self.sources])

    def drop(self, *args, **kwargs):
        """
        Proxy to each source
        :param args:
        :param kwargs:
        :return:
        """
        [source.drop(*args, **kwargs) for source in self.sources]

    def collapse(self) -> Self:
        """
        Collapse source to one
        :return:
        """
        source_cls = type(self).get_source_class()
        data = self.df
        data["timestamp"] = self.T

        source = source_cls(
            source_name=":memory:",
            index=0,
            data=data,
            Y_true=self.Y_true,
            Y_pred=self.Y_pred,
        )

        return type(self)(sources=[source])

    def assert_non_overlapping(self):
        """
        Assert that there are no overlapping timestamps
        :return:
        """
        for a, b in combinations(self.sources, 2):
            a.assert_non_overlapping(b)
