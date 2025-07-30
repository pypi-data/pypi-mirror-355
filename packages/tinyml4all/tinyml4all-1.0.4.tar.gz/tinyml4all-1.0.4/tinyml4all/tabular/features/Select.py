from typing import Any, Literal, Union

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.feature_selection import (
    SelectKBest,
    f_classif,
    f_regression,
    RFE,
    SequentialFeatureSelector,
)

from tinyml4all.support import numeric
from tinyml4all.support.types import ArrayOfStrings, as_list_of_strings, coalesce, cast
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock


class Select(ProcessingBlock):
    """
    Select a subset of columns.
    Can be manually specified, or automatically selected by a feature selector.
    """

    def __init__(
        self,
        include: ArrayOfStrings = None,
        sequential: Union[int, Literal["auto"]] = None,
        univariate: int = None,
        rfe: int = None,
        direction: Literal["forward", "backward"] = "forward",
        estimator: Any = None,
        exclude: ArrayOfStrings = None,
        **kwargs,
    ):
        """

        :param include: manually specify columns to keep
        :param sequential: if set, use Sequential feature selection
        :param univariate: if set, use univariate feature selection
        :param rfe: if set, use recursive feature elimination
        :param direction: if using sequential, specify the direction
        :param estimator: if using sequential or rfe, use this estimator
        param exclude: manually exclude columns
        """
        super().__init__()

        assert (
            (include is not None)
            or (univariate is not None)
            or (rfe is not None)
            or (sequential is not None)
            or (exclude is not None)
        ), (
            "You must specify at least one of include, exclude, univariate, rfe or sequential"
        )

        self.columns = None
        self.config = dict(
            include=as_list_of_strings(include),
            exclude=as_list_of_strings(exclude),
            kbest=SelectKBest(k=cast(univariate, int)) if univariate else None,
            rfe={"k": cast(rfe, int), "estimator": estimator},
            sequential={
                "k": cast(sequential, int),
                "direction": direction,
                "estimator": estimator,
            },
        )

    def __str__(self) -> str:
        """
        Get string representation
        :return:
        """
        if self.columns is not None:
            return f"Select(columns={str(list(self.columns))})"

        return f"Select(config={str(self.config)})"

    def fit(self, dataset, *args, **kwargs):
        """
        Fit
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        X = numeric(dataset.df, boolean=True)
        self.columns = dataset.columns

        if kwargs.get("task") == "regression":
            score_func = f_regression
            default_estimator = RandomForestRegressor(
                n_estimators=7, max_depth=8, min_samples_leaf=5
            )
        else:
            score_func = f_classif
            default_estimator = RandomForestClassifier(
                n_estimators=7, max_depth=8, min_samples_leaf=5
            )

        # manually specify columns
        if len(coalesce(self.config["include"], [])) > 0:
            self.columns = self.config["include"]
        # select using k-best
        elif self.config["kbest"] is not None:
            kbest = self.config["kbest"]
            kbest.score_func = score_func
            kbest.fit(X, dataset.Y_true)

            self.columns = kbest.get_feature_names_out()
        # rfe
        elif (k := self.config["rfe"]["k"]) is not None:
            estimator = coalesce(self.config["rfe"]["estimator"], default_estimator)
            rfe = RFE(estimator, n_features_to_select=k)
            rfe.fit(X, dataset.Y_true)

            self.columns = rfe.get_feature_names_out()
        # sequential
        elif (k := self.config["sequential"]["k"]) is not None:
            direction = self.config["sequential"]["direction"]
            estimator = coalesce(
                self.config["sequential"]["estimator"], default_estimator
            )
            sequential = SequentialFeatureSelector(
                estimator, n_features_to_select=k, direction=direction
            )
            sequential.fit(X, dataset.Y_true)

            self.columns = sequential.get_feature_names_out()

        # exclude specific columns
        if len(self.config["exclude"] or []):
            self.columns = [
                col for col in self.columns if col not in self.config["exclude"]
            ]

        assert len(self.columns) > 0, "No columns selected"

    def transform(self, dataset, *args, **kwargs) -> dict:
        """

        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        assert self.columns is not None, "Unfitted"

        return {"df": dataset.df[self.columns]}
