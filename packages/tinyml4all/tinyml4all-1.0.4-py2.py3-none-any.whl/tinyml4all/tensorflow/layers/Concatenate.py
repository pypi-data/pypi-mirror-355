from tinyml4all.tensorflow.layers.Layer import Layer


class Concatenate(Layer):
    """
    Proxy to tf.Concatenate
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import Concatenate as Base

        self.base = lambda **_: Base(*args, **kwargs)
