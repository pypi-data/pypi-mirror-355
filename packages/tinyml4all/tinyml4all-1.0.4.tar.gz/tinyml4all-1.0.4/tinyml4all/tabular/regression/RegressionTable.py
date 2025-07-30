from math import sqrt

import numpy as np
from prettytable import PrettyTable
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score,
)

from tinyml4all.tabular.common.Table import Table
from tinyml4all.tabular.regression.ScatterLinePlot import ScatterLinePlot
from tinyml4all.tabular.regression.ScatterPlot import ScatterPlot


class RegressionTable(Table):
    """
    Table for regression
    """

    @property
    def scatter(self) -> ScatterPlot:
        """
        Get scatter plotter
        :return:
        """
        return ScatterPlot(self)

    @property
    def plot_predictions(self) -> ScatterLinePlot:
        """
        Get instance of plotter
        :return:
        """
        return ScatterLinePlot(self)

    def regression_report(self):
        """
        Get regression report
        :return:
        """
        assert any(y_pred is not None for y_pred in self.Y_pred), (
            "No predictions available"
        )

        # sort by true values
        idx = np.argsort(self.Y_true)
        y_true = self.Y_true[idx]
        y_pred = self.Y_pred[idx]

        metrics = PrettyTable(["MAE", "RMSE", "MAPE", "R^2"])
        metrics.add_row(
            [
                "%.2f" % mean_absolute_error(y_true, y_pred),
                "%.2f" % sqrt(mean_squared_error(y_true, y_pred)),
                "%d%%" % (100 * mean_absolute_percentage_error(y_true, y_pred)),
                "%.2f" % r2_score(y_true, y_pred),
            ]
        )

        return str(metrics)
