from typing import List, Generator, Tuple

import numpy as np
from pandas import DataFrame
from sklearn.metrics import classification_report

from tinyml4all.support import pretty_confusion_matrix
from tinyml4all.support.traits.HasClassmap import HasClassmap
from tinyml4all.tabular.classification.Pairplot import Pairplot
from tinyml4all.tabular.classification.Scatter import Scatter
from tinyml4all.tabular.common.Source import Source
from tinyml4all.tabular.common.Table import Table


class ClassificationTable(Table, HasClassmap):
    """
    Table for classification
    """

    def __init__(self, sources: List[Source]):
        """
        Constructor
        :param sources:
        """
        Table.__init__(self, sources=sources)
        # always use string targets
        self.set_targets(
            values=[str(y) if y is not None else None for y in self.Y_true]
        )

    def __repr__(self) -> str:
        """
        Get string representation
        :return:
        """
        # todo
        return str(self.df)

    @property
    def Y_true_indices(self) -> np.ndarray:
        """
        Get Y_true as numeric indices
        :return:
        """
        classmap = self.classmap

        return np.asarray(
            [classmap.get(y_true, None) for y_true in self.Y_true], dtype=int
        )

    @property
    def groups(self) -> Generator[Tuple[str, DataFrame], None, None]:
        """
        Group by label

        :return:
        """
        df = self.df
        df["__label__"] = self.Y_true

        for label, group in df.groupby("__label__"):
            yield label, group.drop(columns="__label__")

    @property
    def scatter(self) -> Scatter:
        """
        Get scatter plotter
        :return:
        """
        return Scatter(self)

    @property
    def pairplot(self) -> Pairplot:
        """
        Get pairplot plotter
        :return:
        """
        return Pairplot(self)

    def classification_report(self) -> str:
        """
        Get classification report
        :return:
        """
        labels = [str(label) for label in self.unique_labels]
        classmap = {label: i for i, label in enumerate(labels)}
        Y_pred = [classmap.get(str(y)) for y in self.Y_pred if y is not None]
        Y_true = [
            classmap.get(str(y))
            for y, pred in zip(self.Y_true, self.Y_pred)
            if pred is not None
        ]

        return "\n".join(
            [
                classification_report(
                    Y_true,
                    Y_pred,
                    target_names=labels,
                    zero_division=np.nan,
                ),
                pretty_confusion_matrix(
                    Y_true,
                    Y_pred,
                    target_names=labels,
                ),
            ]
        )
