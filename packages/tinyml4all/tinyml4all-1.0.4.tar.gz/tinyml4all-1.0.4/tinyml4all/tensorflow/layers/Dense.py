from tinyml4all.tensorflow.layers.Layer import Layer
from tinyml4all.tensorflow.layers.mixins.IsFlat import IsFlat


class Dense(IsFlat, Layer):
    """
    Proxy to tf.Dense
    """

    def __init__(self, units: int, activation: str = "relu", **kwargs):
        """
        Constructor
        :param units:
        :param activation:
        :param kwargs:
        """
        from tensorflow.keras.layers import Dense as Base

        self.base = lambda **_: Base(units=units, activation=activation, **kwargs)

    @property
    def tflm_name(self) -> str:
        """
        Get name in Arduino environment
        :return:
        """
        return "FullyConnected"
