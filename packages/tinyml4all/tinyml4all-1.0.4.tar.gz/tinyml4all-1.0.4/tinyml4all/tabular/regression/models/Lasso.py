from sklearn.linear_model import Lasso as Base

from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.regression.models import Linear
from tinyml4all.tabular.regression.models.Estimator import Estimator


class Lasso(Linear):
    """
    Proxy to sklearn.linear_model.Lasso
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        Estimator.__init__(self)

        self.estimator = Base(*args, **kwargs)

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return "tabular.regression.models.Linear", super().get_template()
