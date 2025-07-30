from tinyml4all.tensorflow.layers.Layer import Layer


class LeakyReLU(Layer):
    """
    Proxy to tf.LeakyReLU
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import LeakyReLU as Base

        self.base = lambda **_: Base(*args, **kwargs)

    @property
    def tflm_name(self):
        return "LeakyRelu"
