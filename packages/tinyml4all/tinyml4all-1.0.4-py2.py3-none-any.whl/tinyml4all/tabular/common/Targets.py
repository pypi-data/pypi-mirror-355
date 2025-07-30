from typing import Self, Union, List

import numpy as np


class Targets:
    """
    Table targets (either regression or classification)
    """

    def __init__(self, table: "Table"):
        """
        Constructor
        :param table:
        """
        self.table = table

    @property
    def values(self) -> Self:
        """
        Legacy for book consistency
        :return:
        """
        return self

    @property
    def numeric(self) -> np.ndarray:
        """
        Get numeric targets
        :return:
        """
        values = self.table.Y_true

        if hasattr(self.table, "unique_labels"):
            labels = self.table.unique_labels
            values = [labels.index(y) for y in values]

        return np.asarray(values)

    @property
    def unique_labels(self) -> Union[List[str], None]:
        """
        Get unique labels
        :return:
        """
        return getattr(self.table, "unique_labels", None)
