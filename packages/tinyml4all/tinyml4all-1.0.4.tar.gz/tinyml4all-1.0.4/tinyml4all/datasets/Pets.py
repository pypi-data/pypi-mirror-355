import os.path
from functools import cached_property
from glob import glob
from typing import Self

import numpy as np
from PIL import Image


class PetsLoader:
    """
    Load pets toy dataset (dogs vs cats)
    """

    def __init__(self):
        """
        Constructor
        """
        self._X = None
        self._Y = None

    @cached_property
    def X(self) -> np.ndarray:
        """
        Load X
        :return:
        """
        return self.load()._X

    @cached_property
    def Y(self) -> np.ndarray:
        """
        Load Y
        :return:
        """
        return self.load()._Y

    def load(self) -> Self:
        """
        Load data
        :return:
        """
        if self._X is None:
            root = os.path.join(
                os.path.dirname(__file__),
                "..",
                "transpile",
                "templates",
                "__assets__",
                "data",
            )
            dogs = [
                np.asarray(Image.open(filename), dtype=float) / 255
                for filename in glob(os.path.join(root, "dogs", "*.jpg"))
            ]
            cats = [
                np.asarray(Image.open(filename), dtype=float) / 255
                for filename in glob(os.path.join(root, "dogs", "*.jpg"))
            ]
            self._X = np.vstack([dogs, cats])
            self._Y = np.concatenate([np.zeros(len(dogs)), np.ones(len(cats))])

        return self


Pets = PetsLoader()
