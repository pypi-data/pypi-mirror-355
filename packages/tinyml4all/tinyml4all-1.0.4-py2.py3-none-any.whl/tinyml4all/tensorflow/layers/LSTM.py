from typing import Any

import numpy as np

from tinyml4all.tensorflow.layers.Layer import Layer


class LSTM(Layer):
    """
    Proxy to tf.LSTM
    """

    def __init__(self, units: int, **kwargs):
        """
        Constructor
        :param units:
        :param activation:
        :param kwargs:
        """
        from tensorflow.keras.layers import LSTM as Base

        # all layers must have unroll=True
        # all but the last layer must have return_sequences=True
        # (fixed at resolution time)
        kwargs.update(unroll=True, return_sequences=False)

        self.base = lambda **_: Base(units=units, **kwargs)

    @property
    def tflm_name(self) -> str:
        """
        Get name in Arduino environment
        :return:
        """
        return "UnidirectionalSequenceLSTM"

    @property
    def tflm_dependencies(self):
        return [
            "Shape",
            "Reshape",
            "StridedSlice",
            "Pack",
            "Fill",
            "Transpose",
            "While",
            "Less",
            "Add",
            "Gather",
            "Split",
            "Mul",
            "Minimum",
            "Maximum",
            "Relu",
            "Tanh",
            "Concatenation",
            "Slice",
        ]

    def resolve(self, X: np.ndarray, Y: np.ndarray, input_shape: tuple) -> Any:
        """

        :param X:
        :param Y:
        :param input_shape:
        :return:
        """
        lstm = self.base()

        # handle case where there's a single LSTM layer
        if input_shape[-2] == X.shape[1]:
            lstm.return_sequences = False

        return lstm
