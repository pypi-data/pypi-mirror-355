from typing import Generator

import numpy as np
import pandas as pd

from tinyml4all.time.continuous.classification.ContinuousClassificationTimeSeries import (
    ContinuousClassificationTimeSeries,
)
from tinyml4all.time.continuous.classification.Source import Source
from tinyml4all.time.episodic.classification.EpisodicClassificationTimeSeries import (
    EpisodicClassificationTimeSeries,
)


class BinaryDataset(ContinuousClassificationTimeSeries):
    """
    Binary continuous time classification dataset
    """

    @classmethod
    def convert(cls, ts: EpisodicClassificationTimeSeries, label: str):
        """
        Convert episodic to binary continuous
        :param ts:
        :param label:
        :return:
        """
        episodic_source = ts.reload().collapse().sources[0]
        event_indices = np.argwhere(episodic_source.Y_true == label).flatten()
        Y_true = np.asarray([f"not({label})"] * len(episodic_source))
        Y_true[event_indices] = label

        continuous_source = Source(
            source_name=":memory:",
            index=0,
            data=episodic_source.df,
            Y_true=Y_true,
            T=episodic_source.T,
        )

        return cls(sources=[continuous_source])

    @property
    def event_timestamps(self) -> Generator[pd.Timestamp, None, None]:
        """
        Get event timestamps
        :return:
        """
        for i in np.argwhere(
            [not label.startswith("not(") for label in self.source.Y_true]
        ).flatten():
            yield self.source.T[i]
