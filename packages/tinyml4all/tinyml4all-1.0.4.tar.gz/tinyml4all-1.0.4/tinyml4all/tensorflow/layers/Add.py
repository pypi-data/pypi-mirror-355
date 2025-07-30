from tinyml4all.tensorflow.layers.Layer import Layer


class Add(Layer):
    """
    Proxy to tf.Add
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import Add as Base

        self.base = lambda **_: Base(*args, **kwargs)
