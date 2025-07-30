from typing import List

import numpy as np

from tinyml4all.support import override
from tinyml4all.support.types import TemplateDef
from tinyml4all.transpile.Convertible import Convertible
from tinyml4all.transpile.Variable import Variable


class FeatureExtractor(Convertible):
    """
    Base class for feature extractors
    """

    def __init__(self):
        """
        Constructor
        """
        self.count = None
        self.columns = None

    def __str__(self):
        """
        Get string representation
        :return:
        """
        override(self)

    def __repr__(self):
        """
        Get string representation
        :return:
        """
        return str(self)

    def get_feature_names(self, columns: list[str]) -> list[str]:
        """
        Get feature names
        :param columns:
        :return:
        """
        override(self)

    def save_count(self, data: np.ndarray[float, float]) -> np.ndarray[float, float]:
        """
        Save length of series
        :param data:
        :return:
        """
        self.count = data.shape[1]

        return data

    def save_columns(self, columns: list[str]) -> list[str]:
        """
        Save column names
        :param columns:
        :return:
        """
        self.columns = columns

        return columns

    def get_variables(self) -> List[Variable]:
        """
        Get variables
        :return:
        """
        return [Variable(col, "float") for col in self.get_feature_names(self.columns)]

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {
            "outputs": self.get_variables(),
        }
