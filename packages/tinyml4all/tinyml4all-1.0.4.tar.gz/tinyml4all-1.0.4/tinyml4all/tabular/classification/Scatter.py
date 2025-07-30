from typing import Tuple, List

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from tinyml4all.support import numeric, non_null, unpack_dict
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.colors import hex_colors
from tinyml4all.support.types import TemplateDef
from tinyml4all.transpile.Convertible import Convertible


class Scatter(Convertible):
    """
    Scatter plot
    """

    def __init__(self, table: "ClassificationTable"):
        """
        Constructor
        :param table:
        """
        self.table = table

    def __call__(self, *args, size: int = 6, **kwargs):
        """
        Plot
        :param size: size of the dots
        :param args:
        :param kwargs:
        :return:
        """
        df = numeric(self.table.df)
        points, ax, ay = self.get_points(df)
        chart = Chartjs(type="bubble", ax=ax, ay=ay)

        if title := kwargs.pop("title", ""):
            chart.set_title(title)

        labels, true_labels, pred_labels = self.get_labels()
        points["label"] = labels
        points["true"] = true_labels
        points["pred"] = pred_labels
        points["wrong"] = [
            y_pred is not None and y_true != y_pred
            for y_true, y_pred in zip(true_labels, pred_labels)
        ]

        num_labels = len(set(labels))
        border_colors = hex_colors(kwargs.get("palette", "tab10"), n_colors=num_labels)
        background_colors = hex_colors(
            kwargs.get("palette", "tab10"), n_colors=num_labels, opacity=0.5
        )

        for i, (label, label_df) in enumerate(points.groupby("label")):
            chart.add_dataset(
                label=str(label),
                data=[
                    {
                        "x": x,
                        "y": y,
                        "r": size * 2 if wrong else size,
                        "tooltip": non_null(
                            [
                                f"True label: {true}",
                                f"Predicted label: {pred}"
                                if pred is not None
                                else None,
                            ]
                        ),
                    }
                    for row in label_df.to_dict("records")
                    for x, y, true, pred, wrong in unpack_dict(
                        row, "x y true pred wrong"
                    )
                ],
                pointStyle=[
                    "circle"
                    if pred is None
                    else ("rectRot" if true == pred else "star")
                    for row in label_df.to_dict("records")
                    for true, pred in unpack_dict(row, "true pred")
                ],
                borderColor=border_colors[i],
                backgroundColor=background_colors[i],
            )

        # show tooltip from points
        chart.custom_tooltip()
        chart.add_content(
            after="""
            <div class="text-center mt-4">
                <p class="text-sm text-slate-600">
                    Hover over a point to see the true/predicted label (if available)
                </p>
                <p class="text-sm text-slate-600 mt-2">
                    Click on the legend names to toggle the corresponding series
                </p>
            </div>
        """
        )

        return chart.render()

    def get_template(self) -> TemplateDef:
        """

        :return:
        """
        return "Chartjs", {}

    def get_points(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, str, str]:
        """
        Get points for scatter plot
        :param df:
        :return:
        """
        match len(df.columns):
            case 1:
                # add fake column
                ax = df.columns[0]
                x = df[ax]

                return pd.DataFrame({"x": x, "y": x}), ax, ax
            case 2:
                # exactly 2 columns
                ax, ay = [col for col in df.columns]

                return pd.DataFrame({"x": df[ax], "y": df[ay]}), ax, ay
            case _:
                # more than 2 columns
                # if table has labels, use tSNE
                if len(self.table.unique_labels) > 1:
                    tsne = TSNE().fit_transform(df, self.table.Y_true)

                    return (
                        pd.DataFrame({"x": tsne[:, 0], "y": tsne[:, 1]}),
                        "tSNE-1",
                        "tSNE-2",
                    )
                # else use PCA
                else:
                    pca = PCA().fit_transform(df.to_numpy())

                    return (
                        pd.DataFrame({"x": pca[:, 0], "y": pca[:, 1]}),
                        "PCA-1",
                        "PCA-2",
                    )

    def get_labels(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Get labels for points
        :return:
        """
        true_labels = [str(y) for y in self.table.Y_true]
        pred_labels = []
        labels = []

        for y_true, y_pred in zip(self.table.Y_true, self.table.Y_pred):
            if y_pred is not None:
                pred_labels.append(str(y_pred))
                labels.append(str(y_true) if y_true == y_pred else "incorrect")
            else:
                pred_labels.append(None)
                labels.append(str(y_true))

        return labels, true_labels, pred_labels
