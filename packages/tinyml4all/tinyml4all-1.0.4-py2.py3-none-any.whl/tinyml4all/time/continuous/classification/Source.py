from collections import Counter
from typing import Generator, Tuple

import numpy as np
import pandas as pd

from tinyml4all.support import plain_filename
from tinyml4all.time.Source import Source as Base


class Source(Base):
    """
    Source for continuous classification time series
    """

    @property
    def groups(
        self,
    ) -> Generator[Tuple[str, pd.Timestamp, pd.Timestamp, pd.DataFrame], None, None]:
        """
        Iterate over groups of labels
        :return:
        """
        labels = pd.Series(self.Y_true).fillna("__NONE__")
        ne = labels.ne(labels.shift()).to_numpy()
        changes = np.concatenate((np.where(ne)[0], [len(labels)]))

        for a, b in zip(changes[:-1], changes[1:]):
            label = labels.iloc[a]
            start_at = self.T[a]
            end_at = self.T[b - 1]

            yield (
                label if label != "__NONE__" else None,
                start_at,
                end_at,
                self.df.iloc[a:b],
            )

    def label_from_source(self, padding: str = None) -> None:
        """
        Apply label to data
        :param padding: skip labelling of external data
        :return:
        """
        label = plain_filename(self.source_name)
        start_at = self.start_at
        end_at = self.end_at

        if padding is not None:
            delta = pd.Timedelta(padding)
            start_at += delta
            end_at -= delta

        self.Y_true = pd.Series([None] * len(self))
        self.Y_true.iloc[(self.T >= start_at) & (self.T <= end_at)] = label
        self.Y_true = self.Y_true.to_numpy()

    def add_label(self, label: str, start_at: str, end_at: str):
        """
        Add label to range
        :param label:
        :param start_at:
        :param end_at:
        :return:
        """
        start_at = pd.Timestamp(start_at)
        end_at = pd.Timestamp(end_at)
        mask = (self.T >= start_at) & (self.T <= end_at)

        self.Y_true = pd.Series(np.where(mask, label, self.Y_true)).to_list()
