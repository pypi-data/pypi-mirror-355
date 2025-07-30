from tinyml4all.tensorflow.layers.Layer import Layer


class PReLU(Layer):
    """
    Proxy to tf.PReLU
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import PReLU as Base

        self.base = lambda **_: Base(*args, **kwargs)

    @property
    def tflm_name(self):
        return "Prelu"
