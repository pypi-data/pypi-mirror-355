import os
from glob import glob
from typing import Union, List, Tuple, Self

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from tinyml4all.support import slice_to_indices, non_null, load_sources, numeric
from tinyml4all.support.traits.HasSources import HasSources
from tinyml4all.support.traits.IsPickleable import IsPickleable
from tinyml4all.support.types import Array, coalesce, is_iterable
from tinyml4all.tabular.common.Source import Source
from tinyml4all.tabular.common.Targets import Targets


class Table(HasSources, IsPickleable):
    """
    Base class for tabular data
    """

    @classmethod
    def get_source_class(cls) -> type:
        """
        Get source class
        :return:
        """
        return Source

    @classmethod
    def merge(cls, table: "Table", update: dict) -> "Table":
        """
        Merge table with update
        :param table:
        :param update:
        :return:
        """
        assert len(table.sources) == 1, "Table is not collapsed"

        source_cls = cls.get_source_class()
        update = {
            **table.sources[0].__dict__,
            **update,
            "source_name": ":memory:",
            "index": 0,
        }

        return cls(sources=[source_cls(**update)])

    def __init__(self, sources: List[Source]):
        """
        Constructor
        :param sources:
        """
        HasSources.__init__(self, sources)

    def __str__(self) -> str:
        """
        Get string representation
        :return:
        """
        return str(self.df)

    def __len__(self) -> int:
        """
        Get number of rows
        :return:
        """
        return sum(len(source) for source in self.sources)

    def __getattr__(self, item):
        """
        Proxy unknown attributes to pandas
        :param item:
        :return:
        """
        return getattr(self.df, item)

    def __getitem__(
        self, item: Union[str, int, List[str], Array, slice]
    ) -> Union["Table", dict, Series]:
        """
        Array-like access
        :param item:
        :return:
        """
        if isinstance(item, int):
            return self.get_row(item)

        if isinstance(item, str):
            return self.get_column(item)

        if isinstance(item, slice):
            return self.get_rows(slice_to_indices(item, length=len(self)))

        if is_iterable(item, int):
            return self.get_rows(item)

        # get slice of columns
        assert is_iterable(item, str), (
            "item must be a list of strings to select columns"
        )

        return self.get_columns(item)

    @property
    def targets(self) -> Targets:
        """
        Get targets
        :return:
        """
        return Targets(self)

    @property
    def df(self) -> DataFrame:
        """
        Get data
        :return:
        """
        return pd.concat([source.df for source in self.sources])

    @property
    def numeric(self) -> DataFrame:
        """
        Get numeric data
        :return:
        """
        return numeric(self.df, boolean=True)

    def full(self) -> DataFrame:
        """
        Get data + ground truth + predictions
        :return:
        """
        targets = pd.DataFrame({"GROUND TRUTH": self.Y_true, "PREDICTION": self.Y_pred})

        return pd.concat([self.df, targets], axis=1, ignore_index=True)

    def get_row(self, index: int) -> dict:
        """
        Get row by index
        :param index:
        :return:
        """
        source_index, row_index = self.get_source_index(index)
        source = self.sources[source_index]
        row = source.df.iloc[index]
        y_true = source.Y_true[index]
        y_pred = source.Y_pred[index]

        return {**row, **{"y_true": y_true, "y_pred": y_pred}}

    def get_column(self, column: str) -> Series:
        """
        Get column
        :param column:
        :return:
        """
        return Series(
            np.concatenate([source.df[column] for source in self.sources]), name=column
        )

    def get_rows(self, rows: Tuple[int | None, int | None] | Array) -> "Table":
        """

        :param rows:
        :return:
        """
        new_sources: List[Source | None] = [None] * len(self.sources)

        # handle the most generic case of a list of indices
        if isinstance(rows, tuple):
            start = rows[0] or 0
            end = rows[1] or len(self)
            rows = range(start, end)

        for i in rows:
            source_index, row_index = self.get_source_index(i)
            source = self.sources[source_index]

            if new_sources[source_index] is None:
                empty = pd.DataFrame(columns=source.df.columns)
                new_sources[source_index] = Source(
                    source.source_name, index=source.index, data=empty
                )

            row = source.get_row(row_index)
            y_true = source.Y_true[row_index]
            y_pred = source.Y_pred[row_index]
            new_sources[source_index].append_row(row, y_true=y_true, y_pred=y_pred)

        return type(self)(sources=non_null(new_sources))

    def get_columns(self, columns: List[str]) -> "Table":
        """
        Get columns
        :param columns:
        :return:
        """
        return type(self)(
            sources=[source.get_columns(columns) for source in self.sources]
        )

    def set_targets(
        self, *, column: str = None, values: Array = None, rows: tuple = None
    ) -> Self:
        """
        Set target values

        :param column:
        :param values:
        :param rows:
        :return:
        """
        assert column is not None or values is not None, "column or values must be set"
        assert rows is None or isinstance(rows, tuple), (
            "rows must be a tuple (start, end)"
        )

        rows = coalesce(rows, (0, len(self)))
        rows = (coalesce(rows[0], 0), coalesce(rows[1], len(self)))
        iloc = slice(*rows)

        if column is not None:
            values = self.df[column].iloc[iloc]
            [source.drop(columns=[column]) for source in self.sources]

        for i, value in zip(slice_to_indices(iloc, length=len(self)), values):
            source_index, row_index = self.get_source_index(i)
            self.sources[source_index].Y_true[row_index] = value

        return self

    def drop(self, *args, **kwargs) -> None:
        """
        Drop columns
        :param args:
        :param kwargs:
        :return:
        """
        [source.drop(*args, **kwargs) for source in self.sources]

    def get_source_index(self, index: int) -> Tuple[int, int]:
        """
        Get source index and row index
        :param index:
        :return:
        """
        for source_index, source in enumerate(self.sources):
            if index < len(source):
                return source_index, index

            index -= len(source)

        raise IndexError(f"Index {index} out of range")
