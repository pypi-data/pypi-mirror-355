from typing import Generator

import numpy as np

from tinyml4all.time.features.FeatureExtractor import FeatureExtractor


class Autocorrelation(FeatureExtractor):
    """
    Compute autocorrelation at lag=1
    """

    def __str__(self):
        """
        Get string representation
        :return:
        """
        return "Autocorrelation(lag=1)"

    def __call__(self, data: np.ndarray[float, float]) -> Generator[float, None, None]:
        """
        Extract autocorrelation
        :param data:
        :return:
        """
        for column in self.save_count(data.T):
            mean = np.mean(column)
            zero_mean = column - mean
            var = np.sum(zero_mean**2)

            yield np.sum(zero_mean[1:] * zero_mean[:-1]) / var

    def get_feature_names(self, columns: list[str]) -> Generator[str, None, None]:
        """
        Get feature names
        :param columns:
        :return:
        """
        for column in self.save_columns(columns):
            yield f"autocorrelation({column})"
