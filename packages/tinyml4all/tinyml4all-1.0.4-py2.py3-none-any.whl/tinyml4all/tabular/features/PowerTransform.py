import numpy as np
from sklearn.preprocessing import PowerTransformer

from tinyml4all.support import numeric, override
from tinyml4all.support.types import ArrayOfStrings, coalesce, TemplateDef
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock


class PowerTransform(ProcessingBlock):
    """
    Power transformation.
    See https://en.wikipedia.org/wiki/Power_transform
    """

    def __init__(self, columns: ArrayOfStrings = None):
        """ """
        super().__init__()
        self.all_columns = None
        self.columns = columns
        self.power = PowerTransformer(method=self.method(), standardize=False)

    def __str__(self) -> str:
        """ """
        return f"{self.method().upper()}(columns={coalesce(self.columns, 'ALL')})"

    def get_template(self) -> TemplateDef:
        """

        :return:
        """
        return {"lambdas": self.power.lambdas_}

    def fit(self, dataset, *args, **kwargs):
        """

        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        df = numeric(dataset.df, boolean=False)
        self.columns = coalesce(self.columns, [col for col in df.columns])
        df = self.remember_working_variables(df[self.columns])
        self.power.fit(self.preprocess(df.to_numpy()))

        return self

    def transform(self, dataset, *args, **kwargs):
        """

        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        df = dataset.df.copy()
        df[self.columns] = self.power.transform(
            self.preprocess(df[self.columns].to_numpy())
        )

        return {"df": df}

    def method(self) -> str:
        """
        Get power transform method
        :return:
        """
        override(self)

    def preprocess(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X before applying power transform, if required
        :param X:
        :return:
        """
        return X
