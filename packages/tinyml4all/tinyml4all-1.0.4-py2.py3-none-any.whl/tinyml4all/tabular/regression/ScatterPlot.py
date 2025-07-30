import numpy as np

from tinyml4all.support import numeric
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.ChartjsCollection import ChartjsCollection
from tinyml4all.support.userwarn import userwarn
from tinyml4all.tabular.regression.support import reg_line


class ScatterPlot:
    """
    Regression scatter plot
    """

    def __init__(self, table: "RegressionTable"):
        """

        :param table:
        """
        self.table = table

    def __call__(
        self, *args, column: str = None, orientation: str = "vertical", **kwargs
    ):
        """
        Draw plot
        :param args:
        :param kwargs:
        :return:
        """
        if orientation != "vertical":
            userwarn("Horizontal orientation has been deprected.")

        charts = ChartjsCollection()
        columns = (
            [column]
            if column is not None
            else numeric(self.table.df, boolean=False).columns.tolist()
        )

        for column in columns:
            chart = Chartjs(
                type="scatter",
                ax=column,
                ay="Ground truth",
                title=f"{column} vs. ground truth",
            )
            x = self.table.df[column].to_numpy()
            sort = np.argsort(x)
            x = x[sort]
            y = self.table.Y_true[sort]

            # group by x and average
            points = {}

            for xi, yi in zip(x, y):
                points.setdefault(xi, []).append(yi)

            points = [{"x": xi, "y": np.mean(ys)} for xi, ys in points.items()]
            points = sorted(points, key=lambda x: x["x"])

            # fit poly line to data
            xu = [point["x"] for point in points]
            yu = [point["y"] for point in points]
            fit = np.polynomial.Polynomial.fit(xu, yu, 2)(xu)
            reg_data = [{"x": xi, "y": yi} for xi, yi in zip(xu, fit)]

            chart.add_dataset(
                column,
                [{"x": xi, "y": yi} for xi, yi in zip(x, y)],
                pointRadius=kwargs.get("pointRadius", 6),
                borderColor="#7DAED9",
                backgroundColor="#7DAED9",
            )
            chart.add_dataset(
                "regression",
                reg_data,
                type="line",
                borderColor="#e74c3c",
                pointRadius=0,
            )
            chart.disable_legend()
            charts.append(chart)

        return charts.render()
