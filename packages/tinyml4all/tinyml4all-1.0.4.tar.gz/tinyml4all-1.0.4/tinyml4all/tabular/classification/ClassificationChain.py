from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.Chain import Chain


class ClassificationChain(Chain):
    """
    Chain for classification
    """

    def __init__(self, *blocks):
        """
        Constructor
        """
        super().__init__(*blocks)
        self.classmap = None

    def __call__(self, dataset, *args, **kwargs):
        """
        Call parent
        :param args:
        :param kwargs:
        :return:
        """
        if not self.fitted:
            self.classmap = dataset.classmap

        return super().__call__(dataset, *args, **kwargs, task="classification")

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return "tabular/Chain", {
            **Chain.get_template(self),
            "task": "classification",
            "classmap": self.classmap,
        }
