from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor

from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.regression.models import DecisionTree
from tinyml4all.tabular.regression.models.Estimator import Estimator


class RandomForest(Estimator):
    """
    Proxy to sklearn.ensemble.RandomForestRegressor
    """

    def __init__(
        self,
        n_estimators: int = 15,
        *,
        max_depth: int = 10,
        min_samples_leaf: int = 5,
        **kwargs,
    ):
        Estimator.__init__(self)

        self.estimator = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            **kwargs,
        )

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """

        def wrap(tree: DecisionTreeRegressor):
            wrapped = DecisionTree()
            wrapped.estimator = tree
            wrapped.input_dtypes = self.input_dtypes
            wrapped.working_dtypes = self.working_dtypes

            return wrapped

        return {"trees": [wrap(tree) for tree in self.estimator.estimators_]}
