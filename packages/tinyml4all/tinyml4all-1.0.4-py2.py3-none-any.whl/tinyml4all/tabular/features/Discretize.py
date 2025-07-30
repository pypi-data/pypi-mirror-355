from sklearn.preprocessing import KBinsDiscretizer

from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock


class Discretize(ProcessingBlock):
    """
    Apply column discretization
    """

    def __init__(
        self,
        column: str,
        threshold: float = None,
        bins: int = None,
        append: str = None,
        flip: bool = False,
        strategy: str = "quantile",
    ):
        """
        Constructor
        :param column: column to discretize
        :param threshold: if given, apply binarization
        :param bins: if given, apply binning
        :param append: if given, create new column with discretized values
        :param flip: if True, flip binarization
        :param strategy: strategy for binning
        """
        super().__init__()

        assert threshold is not None or bins is not None, (
            "You must specify either threshold or bins"
        )

        self.all_columns = None
        self.input_column = column
        self.output_column = append or self.input_column
        self.threshold = threshold
        self.flip = flip
        self.discretizer = (
            KBinsDiscretizer(
                bins, strategy=strategy, encode="ordinal", subsample=10_000
            )
            if bins
            else None
        )

    def __str__(self) -> str:
        """

        :return:
        """
        if self.discretizer is not None:
            return f"Discretize(in={self.input_column}, out={self.output_column}, bins={self.discretizer.n_bins})"

        return f"Discretize(in={self.input_column}, out={self.output_column}, threshold={self.threshold}, flip={self.flip})"

    def fit(self, dataset, *args, **kwargs):
        """
        Fit
        :param dataset:
        :return:
        """
        df = self.remember_working_variables(dataset.df)
        self.all_columns = df.columns

        if self.discretizer is not None:
            self.discretizer.fit(df[[self.input_column]])

    def transform(self, dataset, *args, **kwargs):
        """
        Transform
        :param dataset:
        :return:
        """
        df = dataset.df

        # threshold
        if self.threshold is not None:
            df[self.output_column] = (df[self.input_column] >= self.threshold).astype(
                int
            )

            if self.flip:
                df[self.output_column] = 1 - df[self.output_column]
        # kbins
        else:
            df[self.output_column] = self.discretizer.transform(
                df[[self.input_column]]
            )[:, 0]

        return {"df": df}

    def get_template(self) -> TemplateDef:
        """

        :return:
        """
        return {
            "cmp": "<=" if self.flip else ">=",
            "edges": self.discretizer.bin_edges_[0],
        }
