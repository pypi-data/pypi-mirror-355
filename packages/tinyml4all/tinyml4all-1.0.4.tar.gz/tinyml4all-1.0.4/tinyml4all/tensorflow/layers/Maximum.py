from tinyml4all.tensorflow.layers.Layer import Layer


class Maximum(Layer):
    """
    Proxy to tf.Maximum
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import Maximum as Base

        self.base = lambda **_: Base(*args, **kwargs)
