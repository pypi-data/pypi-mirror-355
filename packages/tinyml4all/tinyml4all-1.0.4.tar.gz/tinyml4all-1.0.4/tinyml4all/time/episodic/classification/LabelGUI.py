from tinyml4all.support import asset, sample_indices, view_html
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.colors import hex_colors, rgba_colors
from tinyml4all.support.types import TemplateDef
from tinyml4all.transpile.Convertible import Convertible


class LabelGUI(Convertible):
    """
    Draw UI for labeling of continuous time series
    """

    def __init__(self, ts: "EpisodicClassificationTimeSeries"):
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
        view_html(self)

    def get_template(self) -> TemplateDef:
        """
        Get template data
        :return:
        """
        chart: Chartjs = self.ts.line(render=False)
        chart.add_content(
            after="""
            <div class="text-center mt-4 flex flex-col gap-4">
                <p class="text-slate-600">
                    To label a new event, position the cursor over the middle of the event and <code>click</code> while pressing <code>shift</code>
                </p>
                <p class="text-slate-600">
                    To zoom in on a region, click and drag the mouse. Double click to reset the zoom.
                </p>
            </div>
        """
        )

        # get labels from annotations (we need the uid to remove them)
        # label_annotations = chart.get_annotations(type="label")

        return {
            "chart": chart.definition,
            "T": [str(t) for t in chart.definition["data"]["labels"]],
            "events": [
                {"label": label, "t": t, "height": height}
                for _, label, t, height in self.ts.events
            ],
        }
