from tinyml4all.tensorflow.layers.Layer import Layer


class ELU(Layer):
    """
    Proxy to tf.ELU
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        from tensorflow.keras.layers import ELU as Base

        self.base = lambda **_: Base(*args, **kwargs)

    @property
    def tflm_name(self):
        return "Elu"
