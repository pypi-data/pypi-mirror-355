from tinyml4all.tensorflow.layers.Layer import Layer
from tinyml4all.tensorflow.layers.MaxPooling2D import MaxPooling2D


class GlobalMaxPooling2D(Layer):
    """
    Proxy to tf.GlobalMaxPooling2D
    In TFLM, global pooling is not available, so we
    use a normal MaxPooling2D layer with the correct shape
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param units:
        :param activation:
        :param args:
        :param kwargs:
        """
        self.base = None

    @property
    def tflm_name(self):
        return "MaxPool2D"

    def resolve(self, input_shape: tuple, **kwargs):
        """
        Resolve layer instance, if needed
        :return:
        """
        return MaxPooling2D(input_shape[1:3]).resolve(input_shape=input_shape, **kwargs)
