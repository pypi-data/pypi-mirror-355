from tinyml4all.tensorflow.layers.Layer import Layer


class Minimum(Layer):
    """
    Proxy to tf.Minimum
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import Minimum as Base

        self.base = lambda **_: Base(*args, **kwargs)
