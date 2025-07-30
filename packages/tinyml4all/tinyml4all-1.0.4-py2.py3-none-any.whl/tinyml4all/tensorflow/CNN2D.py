import numpy as np
from PIL import Image

from tinyml4all.tensorflow.Sequential import Sequential


class CNN2D(Sequential):
    """
    Custom implementation for 2D CNN
    """

    def __init__(self, input_shape: tuple = None):
        """
        Constructor
        :param input_shape:
        """
        super().__init__()
        self.target_shape = input_shape

    def compile(self, X, Y, **kwargs):
        """
        Compile network
        :param X:
        :param Y:
        :return:
        """
        return super().compile(X, Y, task="classification", **kwargs)

    def reshape_x(self, X: np.ndarray) -> np.ndarray:
        """
        Be sure X in range [0, 1] and of the correct shape
        :param X:
        :return:
        """
        # images must be in range [0, 1]
        if np.max(X) > 1:
            X = X.astype(float) / 255

        # resize images to input_shape
        if self.target_shape is not None and self.target_shape != X.shape[1:3]:
            X = np.asarray(
                [
                    np.asarray(
                        Image.fromarray((x * 255).astype(np.uint8)).resize(
                            self.target_shape[::-1]
                        )
                    )
                    for x in X
                ]
            )

        if np.max(X) > 1:
            X = X.astype(float) / 255

        return X

    def representative_iterator(self):
        """
        Iterator for representative dataset quantization
        :return:
        """
        for x in self.representative_dataset:
            # reshape from (h, w, c) to (1, h, w, c)
            yield [np.expand_dims(x, axis=0).astype(np.float32)]
