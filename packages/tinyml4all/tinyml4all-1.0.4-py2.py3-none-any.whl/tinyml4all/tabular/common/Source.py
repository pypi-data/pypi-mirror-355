import os
from typing import List

import numpy as np
import pandas as pd
from pandas import DataFrame
from scipy.linalg import pinvh

from tinyml4all.support import plain_filename
from tinyml4all.support.types import Array, coalesce


class Source:
    """
    Source of tabular data
    """

    @classmethod
    def read_csv(cls, path: str, index: int, **kwargs) -> "Source":
        """
        Read CSV file
        :param path:
        :param index:
        :return:
        """
        return cls(source_name=path, index=index, data=pd.read_csv(path, **kwargs))

    def __init__(
        self,
        source_name: str,
        index: int,
        data: DataFrame = None,
        Y_true: Array = None,
        Y_pred: Array = None,
        **kwargs,
    ):
        """
        Constructor
        :param source_name:
        :param index:
        :param data:
        :param Y_true:
        :param Y_pred:
        """
        self.source_name = source_name
        self.index = index
        self.df: DataFrame = kwargs.get("df", data)
        self.Y_true: Array = coalesce(Y_true, lambda: [None] * len(self.df))
        self.Y_pred: Array = coalesce(Y_pred, lambda: [None] * len(self.df))

    def __len__(self) -> int:
        """
        Get number of rows
        :return:
        """
        return len(self.df)

    @property
    def unique_labels(self) -> List[str]:
        """
        Get unique labels
        :return:
        """
        return sorted(list(set(self.Y_true)))

    def label_from_source(self) -> None:
        """
        Apply label to data
        :return:
        """
        self.Y_true = [plain_filename(self.source_name)] * len(self)

    def update(
        self,
        source_name: str = None,
        index: int = None,
        data: DataFrame = None,
        Y_true: Array = None,
        Y_pred: Array = None,
        input_mask: np.ndarray[bool] = None,
        **kwargs,
    ) -> "Source":
        """
        Update and return new
        :param source_name:
        :param data:
        :param index:
        :param Y_true:
        :param Y_pred:
        :param input_mask:
        :return:
        """
        data = coalesce(data, lambda: self.df.copy())
        input_mask = coalesce(input_mask, lambda: np.ones(len(data), dtype=bool))
        # convert binary mask to indices
        input_mask = np.where(input_mask)[0]

        return type(self)(
            source_name=coalesce(source_name, self.source_name),
            index=coalesce(index, self.index),
            data=coalesce(data, lambda: self.df.copy()).iloc[input_mask],
            Y_true=np.asarray(coalesce(Y_true, lambda: self.Y_true.copy()))[
                input_mask
            ].tolist(),
            Y_pred=np.asarray(coalesce(Y_pred, lambda: self.Y_pred.copy()))[
                input_mask
            ].tolist(),
        )

    def drop(self, *args, **kwargs) -> None:
        """
        Drop columns
        :param args:
        :param kwargs:
        :return:
        """
        self.df.drop(*args, **kwargs, inplace=True)

    def get_row(self, index: int) -> dict:
        """
        Get row by index
        :param index:
        :return:
        """
        return self.df.iloc[index].to_dict()

    def append_row(self, row: dict, y_true=None, y_pred=None) -> None:
        """
        Append row
        :param row:
        :param y_true:
        :param y_pred:
        :return:
        """
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
        self.Y_true = np.concatenate([self.Y_true, [y_true]])
        self.Y_pred = np.concatenate([self.Y_pred, [y_pred]])

    def get_columns(self, columns: List[str]) -> "Source":
        """
        Get columns
        :param columns:
        :return:
        """
        return self.update(data=self.df[columns])
