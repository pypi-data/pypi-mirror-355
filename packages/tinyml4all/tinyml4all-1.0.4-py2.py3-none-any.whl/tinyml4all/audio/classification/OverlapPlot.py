from itertools import groupby
from typing import List

import numpy as np

from tinyml4all.audio.WAV import WAV
from tinyml4all.support import sample_values
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.ChartjsCollection import ChartjsCollection
from tinyml4all.support.colors import hex_colors


class OverlapPlot:
    """
    Draw plot of samples one on top of the other
    """

    def __init__(self, album: "ClassificationAlbum"):
        """

        :param album:
        """
        self.album = album

    def __call__(
        self,
        *args,
        palette: str = "Blues",
        samples_per_class: int = 50,
        points_per_sample: int = 1_000,
        opacity: float = 0.3,
        **kwargs,
    ):
        """
        Draw plot
        :param args:
        :param kwargs:
        :return:
        """

        def make_chart(label: str, files: List[WAV]):
            """
            Define Chart.js chart
            """
            chart = Chartjs(type="line", ax="Time", ay="Amplitude", title=label)
            colors = hex_colors(palette, n_colors=len(files), opacity=opacity)[::-1]

            for file, color in zip(files, colors):
                data = sample_values(file.data, n=points_per_sample)
                chart.add_dataset(
                    label=file.path,
                    data=data,
                    borderColor=color,
                    backgroundColor=color,
                    pointRadius=0,
                )

            chart.set_labels(np.arange(points_per_sample))
            chart.disable_legend()
            chart.add_content(
                after="""
                <div class="text-center mt-4">
                    <p class="text-sm text-slate-600">
                        <code class="bg-stone-200 px-2 rounded text-stone-800 py-1">click + drag</code> to zoom, <code class="bg-stone-200 px-2 rounded text-stone-800 py-1">double click</code> to reset zoom
                    </p>
                </div>
            """
            )

            return chart

        charts = list(
            make_chart(label, list(files))
            for label, files in groupby(
                sorted(self.album.files, key=lambda file: file.dirname),
                key=lambda file: file.dirname,
            )
        )

        ChartjsCollection(charts).render()
