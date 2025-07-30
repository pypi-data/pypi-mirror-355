from tinyml4all.tensorflow.layers.Layer import Layer


class Reshape(Layer):
    """
    Proxy to tf.Reshape
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import Reshape as Base

        self.base = lambda **_: Base(*args, **kwargs)
