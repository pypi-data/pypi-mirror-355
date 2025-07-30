from typing import List, Union, Self, Any

import numpy as np

from tinyml4all.support import view_html
from tinyml4all.support.types import TemplateDef, Array, coalesce
from tinyml4all.transpile.Convertible import Convertible
from tinyml4all.transpile.jinja.JsExpr import JsExpr


class Chartjs(Convertible):
    """
    Generate Chart.js structure
    """

    def __init__(self, type: str, ax: str = "", ay: str = "", **kwargs):
        """
        Constructor

        :param type:
        """
        self.vars = {}
        self.alpine = {"script": "", "template": ""}
        self.definition = {
            "type": type,
            "data": {"datasets": []},
            "options": {
                "responsive": True,
                "animation": False,
                "scales": {
                    "x": {"title": {"display": True, "text": ax}},
                    "y": {"title": {"display": True, "text": ay}},
                },
                "onHover": None,
                "plugins": {
                    "title": {
                        "display": kwargs.get("title", None) is not None,
                        "text": kwargs.get("title", ""),
                        "font": {"size": 18},
                    },
                    "legend": {"display": True},
                    "tooltip": {
                        "callbacks": {
                            "label": JsExpr("() => void 0"),
                            "placeholder": None,
                        }
                    },
                    "zoom": {
                        "zoom": {
                            "mode": "x",
                            "drag": {
                                "enabled": True,
                                "backgroundColor": "rgba(0, 0, 0, 0.1)",
                            },
                        },
                        "pan": {
                            "enabled": False,
                            "mode": "x",
                        },
                    },
                    "annotation": {"annotations": {}},
                },
                "extra": {
                    "content": {
                        "before": "",
                        "after": "",
                    },
                    "variables": {},
                },
            },
            "hooks": {
                "beforeInit": None,
                "afterInit": None,
            },
            **kwargs,
        }

    def set_title(self, title: str):
        """
        Set chart title
        :param title:
        :return:
        """
        self.definition["options"]["plugins"]["title"]["display"] = title != ""
        self.definition["options"]["plugins"]["title"]["text"] = title

    def on_hover(self, callback: JsExpr):
        """
        Modify definition on hover
        :param callback:
        :return:
        """
        self.definition["options"]["onHover"] = callback

    def add_var(self, name: str, value: Any):
        """
        Add variable
        :param name:
        :param value:
        :return:
        """
        self.vars[name] = value
        self.definition["options"]["extra"]["variables"][name] = value

    def set_alpine(self, script: str, template: str):
        """
        Set Alpine script
        :param script:
        :param template:
        :return:
        """
        self.alpine["script"] = script
        self.alpine["template"] = template

    def set_labels(self, labels: Array):
        """
        Set labels
        :param labels:
        :return:
        """
        self.definition["data"]["labels"] = labels

    def disable_legend(self):
        """
        Disable legend
        :return:
        """
        self.definition["options"]["plugins"]["legend"]["display"] = False

    def add_dataset(
        self,
        label: str,
        data: Union[List[dict], List[float], np.ndarray[float]],
        **kwargs,
    ):
        """
        Add dataset definition

        :param label:
        :param data:
        :param kwargs:
        :return:
        """
        self.definition["data"]["datasets"].append(
            {"label": label, "data": data, **kwargs}
        )

    def add_annotation_box(
        self,
        x1: str,
        x2: str,
        y1: float = 0,
        y2: float = 1,
        text: str | dict = None,
        **kwargs,
    ) -> str:
        """
        Add annotation box
        :param x1:
        :param x2:
        :param y1:
        :param y2:
        :param text:
        :param kwargs:
        :return: uid of the annotation
        """
        uid = str(hash(f"{x1}-{x2}-{y1}-{y2}"))
        annotation = {
            "uid": uid,
            "type": "box",
            "xMin": x1,
            "xMax": x2,
            "yMin": JsExpr(f"""(ctx) => percent(ctx.chart.scales.y, {y1})"""),
            "yMax": JsExpr(f"""(ctx) => percent(ctx.chart.scales.y, {y2})"""),
            **kwargs,
        }

        if text is not None:
            if isinstance(text, str):
                text = {"content": text}

            annotation["label"] = {
                "display": True,
                "color": "black",
                "font": {"size": 16},
                "position": {"x": "center", "y": "start"},
                **text,
            }

        self.definition["options"]["plugins"]["annotation"]["annotations"][uid] = (
            annotation
        )

        return uid

    def add_content(self, before: str = "", after: str = ""):
        """
        Add content before and after the chart
        :param before:
        :param after:
        :return:
        """
        self.definition["options"]["extra"]["content"]["before"] += before
        self.definition["options"]["extra"]["content"]["after"] += after

    def add_zoom_instructions(self):
        """
        Add zoom instructions
        :return:
        """
        self.add_content(
            after="""
            <div class="text-center mt-4">
                <p class="text-sm text-slate-600">
                    <code class="bg-stone-200 px-2 rounded text-stone-800 py-1">click + drag</code> to zoom, <code class="bg-stone-200 px-2 rounded text-stone-800 py-1">double click</code> to reset zoom
                </p>
            </div>
        """
        )

    def get_annotations(self, type: str = None) -> List[dict]:
        """
        Get annotations
        :return:
        """
        annotations = list(
            self.definition["options"]["plugins"]["annotation"]["annotations"].values()
        )

        if type is not None:
            annotations = [a for a in annotations if a.get("__type__") == type]

        return annotations

    def before_init(self, js: str):
        """
        Modify definition before initialization
        :param js:
        :return:
        """
        self.definition["hooks"]["beforeInit"] = js

    def custom_tooltip(self, expr: JsExpr = None):
        """
        Customize tooltip
        :return:
        """
        expr = coalesce(
            expr, JsExpr("(ctx) => ctx.dataset.data[ctx.dataIndex].tooltip")
        )
        self.definition["options"]["plugins"]["tooltip"]["callbacks"]["label"] = expr

    def render(self, **kwargs) -> Self:
        """
        Display chart
        :return:
        """
        view_html(self, **kwargs)

        return self

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return "Chartjs/ChartJSX", {"charts": [self.definition]}
