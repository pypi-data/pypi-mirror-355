from collections import namedtuple
from itertools import groupby
from typing import Literal, List

import numpy as np

from tinyml4all.support import sample_values, not_self
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.ChartjsCollection import ChartjsCollection
from tinyml4all.support.colors import hex_colors
from tinyml4all.transpile.jinja.JsExpr import JsExpr

Sample = namedtuple("Sample", ["label", "wav"])


class SequentialPlot:
    """
    Draw plot of samples one after the other
    """

    def __init__(self, album: "ClassificationAlbum"):
        """

        :param album:
        """
        self.album = album
        self.on_tooltip = JsExpr("""({chart, dataIndex}) => {
            /* try to find a filename */
            const breakpoints = chart.options.extra.variables.filename_breakpoints;
            
            for (const breakpoint of breakpoints) {
                if (breakpoint.start <= dataIndex && breakpoint.end >= dataIndex) {
                    const filename = breakpoint.filename;
                    console.log('filename', filename);
                    return filename;
                }
            }
        }""")

    def __call__(
        self,
        *args,
        palette: str = "viridis",
        samples_per_class: int = 10,
        points_per_sample: int = 1_000,
        opacity: float = 0.9,
        padding: float = 0.1,
        stack: Literal["horizontal", "vertical"] = "vertical",
        **kwargs,
    ):
        """
        Draw plot
        :param args:
        :param kwargs:
        :return:
        """
        samples = [
            Sample(label=label, wav=wav)
            for label, files in self.album.groups
            for wav in np.random.choice(files, samples_per_class, replace=False)
        ]

        points_per_sample = min(points_per_sample, len(samples[0].wav))

        if stack == "horizontal":
            self.horizontal(**not_self(locals()))
        else:
            self.vertical(**not_self(locals()))

    def vertical(
        self,
        samples: List[Sample],
        points_per_sample: int,
        padding: float,
        palette: str,
        **kwargs,
    ):
        """
        Draw all samples in a single chart
        :param samples:
        :param points_per_sample:
        :param padding:
        :param palette:
        :param kwargs:
        :return:
        """
        charts = ChartjsCollection()
        # convert padding from fraction to number of samples
        padding = int(points_per_sample * padding)
        colors = hex_colors(palette, n_colors=self.album.num_labels)[::-1]

        for label, label_samples in groupby(samples, key=lambda sample: sample.label):
            chart = Chartjs(type="line", ax="Time", ay="Amplitude", title=label)
            label_samples = list(label_samples)
            start = padding
            total_length = (points_per_sample + padding) * len(label_samples) + padding
            data = np.full(total_length, None)
            filename_breakpoints = []

            for sample in label_samples:
                end = start + points_per_sample
                data[start:end] = sample_values(sample.wav.data, n=points_per_sample)
                filename_breakpoints.append(
                    {"filename": sample.wav.path, "start": start, "end": end}
                )
                start += points_per_sample + padding

            chart.add_dataset(
                label=label, data=data, pointRadius=0, borderColor=colors.pop()
            )
            chart.set_labels(np.arange(total_length))
            chart.disable_legend()
            chart.add_zoom_instructions()
            chart.custom_tooltip(self.on_tooltip)
            chart.add_var("filename_breakpoints", filename_breakpoints)
            charts.append(chart)

        charts.render()

    def horizontal(
        self,
        samples: List[Sample],
        points_per_sample: int,
        palette: str,
        opacity: float,
        padding: float,
        **kwargs,
    ):
        """
        Draw all samples in a single chart
        :param samples:
        :param points_per_sample:
        :param palette:
        :param opacity:
        :param padding:
        :param kwargs:
        :return:
        """
        chart = Chartjs(type="line", ax="Time", ay="Amplitude")
        padding = int(points_per_sample * padding)
        start = padding
        total_length = (points_per_sample + padding) * len(samples) + padding
        colors = hex_colors(palette, n_colors=self.album.num_labels, opacity=opacity)[
            ::-1
        ]

        for label, samples in groupby(samples, key=lambda sample: sample.label):
            data = np.full(total_length, None)

            for i, sample in enumerate(samples):
                end = start + points_per_sample
                data[start:end] = sample_values(sample.wav.data, n=points_per_sample)
                start += points_per_sample + padding

            chart.add_dataset(
                label=label,
                data=data,
                borderColor=colors.pop(),
                pointRadius=0,
            )

        chart.set_labels(np.arange(total_length))
        chart.add_zoom_instructions()
        chart.render()
