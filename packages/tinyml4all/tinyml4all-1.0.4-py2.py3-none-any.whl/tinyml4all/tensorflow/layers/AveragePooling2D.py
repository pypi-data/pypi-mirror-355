from tinyml4all.tensorflow.layers.Layer import Layer


class AveragePooling2D(Layer):
    """
    Proxy to tf.AveragePooling2D
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import AveragePooling2D as Base

        self.base = lambda **_: Base(*args, **kwargs)

    @property
    def tflm_name(self):
        return "AveragePool2D"
