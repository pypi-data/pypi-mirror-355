from typing import Any

import numpy as np


class Layer:
    """
    Base class for layers
    """

    def __getattr__(self, item):
        """
        Proxy
        """
        return getattr(self.base, item)

    @property
    def tflm_name(self) -> str:
        """
        Get name in Arduino environment
        :return:
        """
        return self.__class__.__name__

    @property
    def tflm_dependencies(self) -> list:
        """
        Get dependencies of layer in TFLM
        :return:
        """
        return []

    def resolve(self, X: np.ndarray, Y: np.ndarray, input_shape: tuple) -> Any:
        """
        Resolve layer instance, if needed
        :return:
        """
        instance = self.base

        if type(instance) == type(lambda: 1):
            instance = instance(X=X, Y=Y, input_shape=input_shape)

        return instance
