from itertools import combinations
from typing import Self

from tinyml4all.support import numeric
from tinyml4all.support.types import (
    ArrayOfStrings,
    as_list_of_strings,
    coalesce,
    TemplateDef,
)
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock


class Multiply(ProcessingBlock):
    """
    Polynomial (2) features expansion
    """

    def __init__(
        self,
        columns: ArrayOfStrings = None,
    ):
        """

        :param columns:
        """
        super().__init__()
        self.columns = as_list_of_strings(columns)

    def __str__(self) -> str:
        """

        :return:
        """
        return f"Multiply(columns={coalesce(self.columns, 'ALL')})"

    @property
    def get_template(self) -> TemplateDef:
        return {
            "columns": self.columns,
        }

    def fit(self, dataset, **kwargs) -> Self:
        """
        Fit
        :param dataset:
        :return:
        """
        df = self.remember_working_variables(numeric(dataset.df))
        self.columns = coalesce(self.columns, df.columns)

        return self

    def transform(self, dataset, **kwargs) -> dict:
        """
        Apply combinatorial multiplication

        :param dataset
        :return:
        """
        df = dataset.df.copy()

        # self multiply
        for col in self.columns:
            df[f"{col}_x_{col}"] = df[col].to_numpy() * df[col].to_numpy()

        for a, b in combinations(self.columns, 2):
            df[f"{a}_x_{b}"] = df[a].to_numpy() * df[b].to_numpy()

        return {"df": df}
