import seaborn as sns
from matplotlib import pyplot as plt

from tinyml4all.support import numeric


class Pairplot:
    """
    Scatter plot
    """

    def __init__(self, table: "ClassificationTable"):
        """
        Constructor
        :param table:
        """
        self.table = table

    def __call__(self, *args, **kwargs):
        """
        Plot
        :param args:
        :param kwargs:
        :return:
        """
        df = numeric(self.table.df)
        df["target_name"] = self.table.Y_true

        sns.pairplot(df, hue="target_name")
        plt.show()
