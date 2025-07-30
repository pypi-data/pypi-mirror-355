from typing import Generator

import numpy as np

from tinyml4all.support.types import TemplateDef
from tinyml4all.time.features.FeatureExtractor import FeatureExtractor


class Peaks(FeatureExtractor):
    """
    Compute count of peaks
    """

    def __init__(self, peak_magnitude: float = 0.1):
        """
        Constructor
        """
        super().__init__()
        self.peak_magnitude = peak_magnitude
        self.threashold = None

    def __str__(self):
        """
        Get string representation
        :return:
        """
        return f"Peaks(magnitude={self.peak_magnitude})"

    def __call__(self, data: np.ndarray[float, float]) -> Generator[float, None, None]:
        """
        Count peaks
        :param data:
        :return:
        """
        for column in self.save_count(data.T):
            magnitude = np.max(column) - np.min(column)
            threshold = magnitude * self.peak_magnitude
            is_greater_than_prev = np.abs(column[1:-1] - column[:-2]) > threshold
            is_greater_than_next = np.abs(column[1:-1] - column[2:]) > threshold
            is_peak = np.logical_and(is_greater_than_prev, is_greater_than_next)

            yield is_peak.mean()

    def get_feature_names(self, columns: list[str]) -> Generator[str, None, None]:
        """
        Get feature names
        :param columns:
        :return:
        """
        for column in self.save_columns(columns):
            yield f"peaks({column})"

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {"peak_magnitude": self.peak_magnitude}
