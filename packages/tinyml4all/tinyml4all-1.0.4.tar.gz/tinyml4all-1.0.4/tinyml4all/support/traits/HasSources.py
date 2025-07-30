import os
import pickle
from glob import glob
from io import BytesIO

from pandas import DataFrame
from typing import Self, List

import numpy as np

from tinyml4all.support import load_sources, override


class HasSources:
    """
    Mixin for classes that have sources
    """

    @classmethod
    def get_source_class(cls) -> type[Self]:
        """
        Get source class
        :return:
        """
        override(cls)

    @classmethod
    def from_pandas(cls, df: DataFrame, **kwargs) -> Self:
        """
        Wrap DataFrame into time series
        """
        kwargs.setdefault("source_name", "pandas")
        kwargs.setdefault("index", 0)

        return cls(sources=[cls.get_source_class()(data=df, **kwargs)])

    @classmethod
    def read_csv(cls: type[Self], path: str | BytesIO, **kwargs) -> Self:
        """
        Read CSV file
        :param path:
        :return:
        """
        return cls(sources=[cls.get_source_class().read_csv(path, index=0, **kwargs)])

    @classmethod
    def read_csv_folder(cls: type[Self], folder: str, **kwargs) -> Self:
        """
        Read CSV files from folder
        :param folder:
        :return:
        """
        # todo: remove?
        # if a pickled version exists, load it
        # pickles = glob(os.path.join(folder, "*.pkl"))
        #
        # # single pickled version
        # if len(pickles) == 1 and input("A saved version of this dataset already exists: do you want to load it? [y|N] ").lower().startswith("y"):
        #     with open(pickles[0], "rb") as f:
        #         return pickle.load(f)
        #
        # # multiple pickled versions
        # elif len(pickles) > 1:
        #     print("Multiple saved versions of this dataset exist. How do you want to proceed?")
        #     print("[1] Ignore all saved versions and load from CSV files")
        #
        #     for i, pick in enumerate(pickles):
        #         print(f"[{i+2}] {pick}")
        #
        #     if (choice := int(input("Enter option: "))) and choice > 2:
        #         with open(pickles[choice - 2], "rb") as f:
        #             return pickle.load(f)

        return cls(
            sources=load_sources(
                folder=folder, source_cls=cls.get_source_class(), **kwargs
            )
        )

    def __init__(self, sources: List["Source"]):
        """
        Constructor
        :param sources:
        """
        self.sources = sources

    @property
    def source(self) -> "Source":
        """
        Get source if only one
        :return:
        """
        assert len(self.sources) == 1, "The dataset must be collapsed first"

        return self.sources[0]

    @property
    def Y_true(self) -> np.ndarray:
        """
        Get true labels
        :return:
        """
        return np.concatenate([source.Y_true for source in self.sources])

    @property
    def Y_pred(self) -> np.ndarray:
        """
        Get predicted labels
        :return:
        """
        return np.concatenate([source.Y_pred for source in self.sources])

    @property
    def valid_mask(self) -> np.ndarray:
        """
        Get mask of valid rows
        :return:
        """
        return np.asarray([y is not None for y in self.Y_true], dtype=bool)

    def label_from_sources(self, **kwargs):
        """
        Apply label to all data of each source
        :return:
        """
        for source in self.sources:
            source.label_from_source(**kwargs)

    def collapse(self) -> Self:
        """
        Collapse source to one
        :return:
        """
        source_cls = type(self).get_source_class()
        source = source_cls(
            source_name=":memory:",
            index=0,
            data=self.df,
            Y_true=self.Y_true,
            Y_pred=self.Y_pred,
        )

        return type(self)(sources=[source])
