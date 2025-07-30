from sklearn.linear_model import LinearRegression

from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.regression.models.Estimator import Estimator


class Linear(Estimator):
    """
    Proxy to sklearn.linear_model.LinearRegression
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        Estimator.__init__(self)

        self.estimator = LinearRegression(*args, **kwargs)

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {
            "coefs": self.estimator.coef_,
            "intercept": self.estimator.intercept_,
        }
