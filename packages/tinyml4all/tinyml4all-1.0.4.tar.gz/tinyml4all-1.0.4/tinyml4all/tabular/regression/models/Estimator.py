from typing import Self

import numpy as np

from tinyml4all.support import numeric
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock


class Estimator(ProcessingBlock):
    """
    Base class for tabular regressors
    """

    def __init__(self):
        """
        Constructor
        """
        ProcessingBlock.__init__(self)

        self.estimator = None

    def __str__(self) -> str:
        """
        Get string representation
        :return:
        """
        return str(self.estimator)

    def fit(self, dataset, *args, **kwargs) -> Self:
        """
        Fit
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        assert self.estimator is not None, "Estimator not set"

        is_valid = dataset.valid_mask
        assert np.any(is_valid), "No valid data"

        X = numeric(dataset.df.iloc[is_valid]).to_numpy()
        Y = dataset.Y_true[is_valid].astype(float)

        self.estimator.fit(X, Y)

        return self

    def transform(self, dataset, *args, **kwargs) -> dict:
        """
        Transform
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        is_valid = dataset.valid_mask
        assert np.any(is_valid), "No valid data"

        X = numeric(dataset.df.iloc[is_valid]).to_numpy()
        Y = self.estimator.predict(X).astype(float)

        return {
            "Y_pred": Y,
            "input_mask": is_valid,
        }
