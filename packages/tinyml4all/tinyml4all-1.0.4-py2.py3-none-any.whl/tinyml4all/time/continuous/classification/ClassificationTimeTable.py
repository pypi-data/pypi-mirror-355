from typing import List, Self

from tinyml4all.support import Array
from tinyml4all.tabular.classification import Table
from tinyml4all.tabular.common.Source import Source


class ClassificationTimeTable(Table):
    """
    A Table, with timestamps.
    Used to keep track of windowing timestamps.
    """

    def __init__(self, sources: List[Source], T: Array = None):
        """ """
        super().__init__(sources=sources)
        self.T = T

    def collapse(self) -> Self:
        """
        Override
        :return:
        """
        table = super().collapse()

        return ClassificationTimeTable(sources=table.sources, T=self.T)

    @classmethod
    def merge(cls, table: Self, update: dict) -> Self:
        """

        :param table:
        :param update:
        :return:
        """
        T = update.pop("T", table.T)

        source = {
            **table.sources[0].__dict__,
            **update,
            "source_name": ":memory:",
            "index": 0,
        }

        return cls(sources=[Source(**source)], T=T)
