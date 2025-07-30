from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.Chain import Chain


class RegressionChain(Chain):
    """
    Chain for regression
    """

    def __call__(self, dataset, *args, **kwargs):
        """
        Call parent
        :param args:
        :param kwargs:
        :return:
        """
        return super().__call__(dataset, *args, **kwargs, task="regression")

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return "tabular/Chain", {
            **Chain.get_template(self),
            "task": "regression",
        }
