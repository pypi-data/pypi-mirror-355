from typing import List

from tinyml4all.support import view_html
from tinyml4all.support.Chartjs import Chartjs
from tinyml4all.support.types import TemplateDef, coalesce
from tinyml4all.transpile.Convertible import Convertible


class ChartjsCollection(Convertible):
    """
    Collection of Chartjs objects
    """

    def __init__(self, charts: List[Chartjs] = None):
        """
        Constructor
        :param charts:
        """
        self.charts = coalesce(charts, [])

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return "Chartjs/ChartJSX", {
            "charts": [chart.definition for chart in self.charts]
        }

    def append(self, chart: Chartjs):
        """
        Append chart
        :param chart:
        :return:
        """
        self.charts.append(chart)

    def render(self, **kwargs):
        """
        Display chart
        :return:
        """
        view_html(self, **kwargs)
