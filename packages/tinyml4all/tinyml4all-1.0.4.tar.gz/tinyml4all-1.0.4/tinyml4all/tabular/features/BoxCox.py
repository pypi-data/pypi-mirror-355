import numpy as np

from tinyml4all.tabular.features.PowerTransform import PowerTransform


class BoxCox(PowerTransform):
    """
    Box-Cox power transformation.
    See https://en.wikipedia.org/wiki/Power_transform
    """

    def method(self) -> str:
        """

        :return:
        """
        return "box-cox"

    def preprocess(self, X: np.ndarray) -> np.ndarray:
        """

        :param X:
        :return:
        """
        return np.abs(X)
