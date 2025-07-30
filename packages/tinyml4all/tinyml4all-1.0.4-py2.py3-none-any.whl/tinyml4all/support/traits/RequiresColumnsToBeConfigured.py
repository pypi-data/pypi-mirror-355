from pandas import DataFrame

from tinyml4all.support.types import ArrayOfStrings, coalesce


class RequiresColumnsToBeConfigured:
    """
    Mixin for classes that require column names to be configured
    """

    def __init__(self):
        """ """
        self.all_columns = None

    def set_all_columns(self, columns: ArrayOfStrings | DataFrame):
        """
        Set all columns
        :param columns:
        :return:
        """
        if isinstance(columns, DataFrame):
            df = columns
            columns = [col for col in df.columns]

        self.all_columns = columns

    def configure_columns(self, columns: ArrayOfStrings):
        """
        Configure columns.
        :param columns:
        :return:
        """
        self.all_columns = coalesce(self.all_columns, columns)
