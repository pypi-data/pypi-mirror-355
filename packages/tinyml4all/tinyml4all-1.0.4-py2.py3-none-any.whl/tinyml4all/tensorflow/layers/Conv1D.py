from tinyml4all.tensorflow.layers.Layer import Layer


class Conv1D(Layer):
    """
    Proxy to tf.Conv1D
    In TFLM, Conv1D is not available, so we
    use a Conv2D layer with the correct shape
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

        self.base = lambda **_: Base(filters, (1, kernel_size), *args, **kwargs)

    @property
    def tflm_name(self):
        return "Conv2D"

    def resolve(self, input_shape: tuple, **kwargs):
        """
        Resolve layer instance, if needed
        :return:
        """
        from tensorflow.keras.layers import Reshape

        # if this is the first conv1d layer,
        # input will be (n, w, c)
        # we need to reshape to (n, 1, w, c)
        print("conv1d input shape", input_shape)

        if len(input_shape) == 2:
            w, c = input_shape

            return [Reshape((1, w, c)), self.base()]

        return self.base()
