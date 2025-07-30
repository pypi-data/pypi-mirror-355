class IsFlat:
    """
    Mixin for layers that require flat input
    """

    @property
    def tflm_dependencies(self):
        """
        Get dependencies of layer in TFLM
        :return:
        """
        return ["Shape", "Reshape"]

    def resolve(self, input_shape: tuple, **kwargs):
        """
        If input shape is not flat, flatten it
        :param input_shape:
        :param kwargs:
        :return:
        """
        from tensorflow.keras.layers import Flatten

        if len(input_shape) > 2:
            return [Flatten(), self.base()]

        return self.base()
