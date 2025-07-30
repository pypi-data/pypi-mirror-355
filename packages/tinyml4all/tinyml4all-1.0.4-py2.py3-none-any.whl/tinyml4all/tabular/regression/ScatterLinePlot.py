import numpy as np

from tinyml4all.support.Chartjs import Chartjs


class ScatterLinePlot:
    """
    Draw scatter plot with regression line
    """

    def __init__(self, table: "RegressionTable"):
        """

        :param table:
        """
        self.table = table

    def __call__(self, *args, size: int = 6, color: str = "#7DAED9", **kwargs):
        """
        Draw plot
        :param args:
        :param kwargs:
        :return:
        """

        def reg_func(_x, _y):
            return np.linalg.pinv(_x).dot(_y)

        def as_point(y_true, y_pred, **kwargs) -> dict:
            return {"x": y_true, "y": y_pred, **kwargs}

        # sort by true values
        idx = np.argsort(self.table.Y_true)
        Y_true = self.table.Y_true[idx]
        Y_pred = self.table.Y_pred[idx]

        # taken from sns.regplot > fit_fast
        Y_unique = sorted(np.unique(Y_true))
        grid = np.linspace(np.min(Y_unique), np.max(Y_unique), len(Y_unique))
        X, y = np.c_[np.ones(len(Y_unique)), Y_unique], Y_unique
        grid = np.c_[np.ones(len(grid)), grid]
        reg_line = grid.dot(reg_func(X, y))

        # chart
        chart = Chartjs(type="bubble", ax="Ground truth", ay="Predicted")

        # true vs predicted
        chart.add_dataset(
            label="Predictions",
            order=2,
            borderColor=color,
            backgroundColor=f"{color[:7]}AA",
            data=[
                as_point(y_true, y_pred, r=size)
                for y_true, y_pred in zip(Y_true, Y_pred)
            ],
        )

        # regression line
        chart.add_dataset(
            label="Line fit",
            type="line",
            # draw on top of scatter
            order=1,
            borderColor="#e74c3c",
            backgroundColor="#e74c3c",
            pointRadius=0,
            data=[as_point(y_true, y_reg) for y_true, y_reg in zip(Y_unique, reg_line)],
        )

        return chart.render()
