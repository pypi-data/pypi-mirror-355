from tinyml4all.tensorflow.layers.Layer import Layer


class Conv2D(Layer):
    """
    Proxy to tf.Conv2D
    """

    def __init__(self, filters: int, kernel_size: int = 3, *args, **kwargs):
        """
        Constructor
        :param units:
        :param activation:
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import Conv2D as Base

        self.base = lambda **_: Base(filters, kernel_size, *args, **kwargs)

    @property
    def tflm_dependencies(self):
        return ["Shape", "Reshape", "StridedSlice", "Slice"]
