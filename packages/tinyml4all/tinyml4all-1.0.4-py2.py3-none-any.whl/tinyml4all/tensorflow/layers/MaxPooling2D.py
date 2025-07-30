from tinyml4all.tensorflow.layers.Layer import Layer


class MaxPooling2D(Layer):
    """
    Proxy to tf.MaxPooling2D
    """

    def __init__(self, pool_size: tuple[int, int] = (2, 2), *args, **kwargs):
        """
        Constructor
        :param units:
        :param activation:
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import MaxPooling2D as Base

        self.base = lambda **_: Base(pool_size, *args, **kwargs)

    @property
    def tflm_name(self):
        return "MaxPool2D"
