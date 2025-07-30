from tinyml4all.support import asset, sample_indices
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.colors import hex_colors, rgba_colors


class LabelGUI:
    """
    Draw UI for labeling of continuous time series
    """

    def __init__(self, ts: "TimeSeries"):
        """
        Constructor
        :param ts:
        """
        self.ts = ts

    def __call__(self, *args, **kwargs):
        """
        Draw UI
        :param args:
        :param kwargs:
        :return:
        """
        chart: Chartjs = self.ts.line(*args, **kwargs, render=False)

        # get labels from annotations (we need the uid to remove them)
        label_annotations = chart.get_annotations(type="label")

        # sample timestamps
        num_points = len(chart.definition["data"]["labels"])
        indices = sample_indices(len(self.ts.T), num_points)
        T = [str(t) for t in self.ts.T[indices]]

        chart.add_var("T", T)
        chart.add_var("labelAnnotations", label_annotations)
        chart.add_var(
            "annotationPalette", hex_colors("tab10", n_colors=10, opacity=0.1)
        )
        chart.set_alpine(
            script=asset("time-continuous-label-ui/alpine.js"),
            template=asset("time-continuous-label-ui/alpine.html"),
        )
        chart.before_init(asset("time-continuous-label-ui/beforeInit.js"))

        return chart.render()
