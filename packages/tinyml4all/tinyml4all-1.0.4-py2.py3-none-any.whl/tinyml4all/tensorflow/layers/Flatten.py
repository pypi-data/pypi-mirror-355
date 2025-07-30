from tinyml4all.tensorflow.layers.Layer import Layer


class Flatten(Layer):
    """
    Proxy to tf.Flatten
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import Flatten as Base

        self.base = lambda **_: Base(*args, **kwargs)

    @property
    def tflm_name(self):
        return "Reshape"
