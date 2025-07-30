import os.path
from bisect import bisect_left
from datetime import timedelta
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from tinyml4all.support import numeric, not_self, Array, sample_indices, plain_filename
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.colors import hex_colors
from tinyml4all.transpile.Convertible import Convertible


class Line(Convertible):
    """
    Line plot of time series
    """

    def __init__(self, ts: "EpisodicClassificationTimeSeries"):
        """
        Constructor
        :param ts:
        """
        self.ts = ts

    def __call__(
        self,
        *args,
        title: str = "",
        normalize: bool = False,
        clip: Tuple[float, float] = None,
        line_palette: str = "magma",
        point_palette: str = "viridis",
        max_points: int = 5_000,
        render: bool = True,
        **kwargs,
    ) -> Chartjs:
        """
        Draw plot
        :param title:
        :param normalize: if True, all values are scaled between -1 and 1
        :param clip: if set, all values are clipped to this range
        :param line_palette: palette for data lines
        :param point_palette: palette for points backgrounds
        :param max_points: limit the number of points to render (faster performance)
        :param render: if True, render the chart (when False, allows to modify the chart afterwards)
        :param args:
        :param kwargs:
        :return:
        """
        df = numeric(self.ts.df, boolean=False)
        T = [str(t) for t in self.ts.T]
        chart = Chartjs(type="line", title=title, ax="Timestamp", ay="Data")

        # sample if necessary
        if len(df) > max_points:
            indices = sample_indices(len(df), max_points)
            df = df.iloc[indices]
            T = np.asarray(T)[indices].tolist()

        labels = self.format_labels(T)

        self.draw_lines(**not_self(locals()))
        self.draw_sources(**not_self(locals()))
        self.draw_events(**not_self(locals()))

        chart.set_labels(labels)

        if render:
            chart.render()

        return chart

    def format_labels(self, T: List[str]) -> List[str]:
        """
        Format labels based on total duration
        :param T:
        :return:
        """
        T = pd.to_datetime(T)
        duration = pd.to_timedelta(T[-1] - T[0])

        return [t.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3].replace(" ", "T") for t in T]

        # todo: remove?
        # if duration > timedelta(days=1):
        #     return [t.strftime("%Y-%m-%d %H:%M") for t in T]
        # elif duration > timedelta(hours=1):
        #     return [t.strftime("%Y-%m-%d %H:%M") for t in T]
        # elif duration > timedelta(minutes=1):
        #     return [t.strftime("%H:%M:%S.%f")[:-3] for t in T]

    def draw_lines(
        self,
        chart: Chartjs,
        df: pd.DataFrame,
        labels: Array,
        line_palette: str,
        normalize: bool,
        clip: Tuple[float, float],
        **kwargs,
    ):
        """
        Draw lines of data
        :return:
        """
        line_colors = hex_colors(line_palette, n_colors=len(df.columns))

        for i, (col, color) in enumerate(zip(df.columns, line_colors)):
            values = df[col].to_numpy()

            if clip:
                values = np.clip(values, *clip)

            if normalize:
                values = (
                    MinMaxScaler(feature_range=(-1, 1))
                    .fit_transform(values[:, np.newaxis])
                    .flatten()
                )

            chart.add_dataset(
                label=col,
                type="line",
                data=values,
                borderColor=color,
                pointRadius=0,
                showLine=True,
                order=0,
            )

    def draw_sources(self, chart: Chartjs, T: Array, labels: Array, **kwargs):
        """
        Draw sources
        :param chart:
        :param T:
        :param labels:
        :return:
        """
        bg_colors = hex_colors("tab10", n_colors=len(self.ts.sources), opacity=0.05)

        for source, color in zip(self.ts.sources, bg_colors):
            a = bisect_left(T, str(source.T[0]))
            b = bisect_left(T, str(source.T[-1]))
            chart.add_annotation_box(
                text=f"source: {os.path.basename(source.source_name)}",
                x1=labels[a],
                x2=labels[b - 1],
                y1=0.93,
                backgroundColor=color,
            )

    def draw_events(
        self, chart: Chartjs, point_palette: str, T: Array, labels: List[str], **kwargs
    ):
        """
        Draw events
        :param chart:
        :param point_palette:
        :param T:
        :param labels:
        :param kwargs:
        :return:
        """
        point_colors = {
            label: color
            for label, color in zip(
                self.ts.unique_labels,
                hex_colors(point_palette, n_colors=len(self.ts.unique_labels)),
            )
        }
        scatter_data = []

        for source, label, t, height in self.ts.events:
            index = bisect_left(T, str(t))
            scatter_data.append(
                {
                    "x": labels[index],
                    "t": str(t),
                    "y": height,
                    "label": label,
                    "tooltip": f"Label: {label} at {str(t)}",
                    "backgroundColor": point_colors[label],
                    "__source__": source.basename,
                }
            )

        chart.add_var("existingPalette", point_colors)
        chart.add_var("newPalette", hex_colors("tab10", n_colors=10))
        chart.add_dataset(
            label="Events",
            type="scatter",
            showLine=False,
            data=scatter_data,
            backgroundColor=[point["backgroundColor"] for point in scatter_data],
            pointRadius=6,
        )

        # show tooltip from points
        chart.custom_tooltip()
