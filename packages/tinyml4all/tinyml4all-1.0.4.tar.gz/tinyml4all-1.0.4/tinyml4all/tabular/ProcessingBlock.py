from typing import Any, Union, Literal

from pandas import DataFrame

from tinyml4all.support import override
from tinyml4all.support.override_help import override_help
from tinyml4all.support.traits.RequiresColumnsToBeConfigured import (
    RequiresColumnsToBeConfigured,
)
from tinyml4all.transpile.Convertible import Convertible
from tinyml4all.transpile.Jsonable import Jsonable
from tinyml4all.transpile.Variable import Variable


class ProcessingBlock(Convertible, Jsonable, RequiresColumnsToBeConfigured):
    """
    Block of a chain for tables (and derivatives)
    """

    def __init__(self):
        """
        Constructor
        """
        RequiresColumnsToBeConfigured.__init__(self)

        self.fitted = False
        self.input_dtypes = None
        self.output_dtypes = None
        self.working_dtypes = None

        # allow custom help messages for ProcessingBlock
        override_help()

    def __repr__(self) -> str:
        """
        Convert to string
        :return:
        """
        return str(self)

    def __call__(self, dataset, *args, **kwargs) -> Any:
        """
        Fit transform
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        dataset = dataset.collapse()

        if not self.fitted:
            self.remember_input(dataset)
            self.fit(dataset, *args, **kwargs)
            self.fitted = True

        update = self.transform(dataset, *args, **kwargs)
        # allow blocks to change dataset type
        new_type = update.pop("type", type(dataset))
        new_dataset = new_type.merge(dataset, update)

        return self.remember_output(new_dataset)

    def remember_input(self, input: Union[DataFrame, "Table"]) -> DataFrame:
        """
        Store number and types of inputs
        :param input:
        :return:
        """
        self.set_all_columns(input.columns)

        return self.remember_variables(input, target="input")

    def remember_output(self, output: Union[DataFrame, "Table"]) -> Any:
        """
        Store number and types of outputs
        :param output:
        :return:
        """
        return self.remember_variables(output, target="output")

    def remember_working_variables(self, data: Union[DataFrame, "Table"]) -> Any:
        """
        Store number and types of outputs
        :param data:
        :return:
        """
        self.set_all_columns(data.columns)

        return self.remember_variables(data, target="working")

    def remember_variables(
        self,
        data: Union[DataFrame, "Table"],
        target: Literal["input", "output", "working"],
    ):
        """
        Store number and types of variables
        :param data:
        :param target:
        :return:
        """
        if hasattr(data, "df"):
            self.remember_variables(data.df, target=target)
        else:
            variables = [
                Variable(str(col), dtype) for col, dtype in data.dtypes.items()
            ]

            match target:
                case "input":
                    self.input_dtypes = variables
                case "output":
                    self.output_dtypes = variables
                case "working":
                    self.working_dtypes = variables

        # todo: more output types?

        return data

    def configure_from(self, dataset: Any, **kwargs):
        """
        Configure transformer from dataset.
        Meant to be overridden.
        :param dataset:
        :return:
        """
        pass

    def unfit(self):
        """
        Unfit
        :return:
        """
        self.fitted = False

    def fit(self, dataset, *args, **kwargs) -> Any:
        """
        Fit
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        override(self)

    def transform(self, dataset, *args, **kwargs) -> Any:
        """
        Transform
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        override(self)
