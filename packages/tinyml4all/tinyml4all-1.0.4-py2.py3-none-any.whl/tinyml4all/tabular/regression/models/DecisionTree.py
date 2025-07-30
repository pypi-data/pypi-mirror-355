from sklearn.tree import DecisionTreeRegressor

from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.classification.models.Estimator import Estimator


class DecisionTree(Estimator):
    """
    Proxy to sklearn.tree.DecisiontTreeRegressor
    """

    def __init__(self, *args, max_depth: int = 10, min_samples_leaf: int = 5, **kwargs):
        Estimator.__init__(self)

        self.estimator = DecisionTreeRegressor(
            *args, max_depth=max_depth, min_samples_leaf=min_samples_leaf, **kwargs
        )

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {
            "left": self.estimator.tree_.children_left,
            "right": self.estimator.tree_.children_right,
            "features": self.estimator.tree_.feature,
            "thresholds": self.estimator.tree_.threshold,
            "values": self.estimator.tree_.value,
        }
