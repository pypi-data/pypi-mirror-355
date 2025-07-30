from tinyml4all.tensorflow.layers.Layer import Layer


class DepthwiseConv2D(Layer):
    """
    Proxy to tf.DepthwiseConv2D
    """

    def __init__(self, kernel_size: int = 3, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import DepthwiseConv2D as Base

        self.base = lambda **_: Base(kernel_size, *args, **kwargs)
