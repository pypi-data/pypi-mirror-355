from typing import Any, Self

from tinyml4all.support import numeric
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock


class Estimator(ProcessingBlock):
    """
    Base class for tabular classifiers
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
        df = numeric(dataset.df.iloc[is_valid])
        X = self.remember_input(df).to_numpy()
        Y = dataset.Y_true[is_valid]

        assert len(set(Y)) > 1, "Cannot train classifier with only one class"

        # Y is a list of strings, convert to int
        classmap = dataset.classmap
        Y = [classmap.get(y) for y in Y]

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
        df = numeric(dataset.df.iloc[is_valid])
        X = df.to_numpy()
        Y = self.estimator.predict(X)

        # Y is a list of ints, convert to strings
        inverse_classmap = dataset.inverse_classmap
        Y = [inverse_classmap.get(y) for y in Y]

        return {
            "Y_pred": Y,
            "input_mask": is_valid,
        }
