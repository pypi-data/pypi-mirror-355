from typing import Generator

import numpy as np

from tinyml4all.support.types import TemplateDef
from tinyml4all.time.features.FeatureExtractor import FeatureExtractor
from tinyml4all.transpile.Convertible import Convertible
from tinyml4all.transpile.Variable import Variable


class CountAboveMean(FeatureExtractor):
    """
    Compute count of values above mean
    """

    def __str__(self):
        """
        Get string representation
        :return:
        """
        return "CountAboveMean()"

    def __call__(self, data: np.ndarray[float, float]) -> Generator[float, None, None]:
        """
        Count values above mean
        :param data:
        :return:
        """
        for column in self.save_count(data.T):
            yield np.mean(column > np.mean(column))

    def get_feature_names(self, columns: list[str]) -> Generator[str, None, None]:
        """
        Get feature names
        :param columns:
        :return:
        """
        for column in self.save_columns(columns):
            yield f"count_above_mean({column})"
