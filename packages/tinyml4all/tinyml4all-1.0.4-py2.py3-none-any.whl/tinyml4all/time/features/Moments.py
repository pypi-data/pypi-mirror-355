from typing import List, Generator

import numpy as np

from tinyml4all.support.types import TemplateDef
from tinyml4all.time.features.FeatureExtractor import FeatureExtractor
from tinyml4all.transpile.Variable import Variable


class Moments(FeatureExtractor):
    """
    Extract statistical moments
    """

    def __str__(self) -> str:
        """
        Get string representation
        :return:
        """
        return "Moments()"

    def __call__(self, data: np.ndarray[float, float]) -> Generator[float, None, None]:
        """
        Extract moments
        :param data:
        :return:
        """
        for column in self.save_count(data.T):
            column_abs = np.abs(column)

            yield np.min(column)
            yield np.max(column)
            yield np.mean(column)
            yield np.min(column_abs)
            yield np.max(column_abs)
            yield np.mean(column_abs)
            # std
            yield np.sqrt(((column - np.mean(column)) ** 2).mean())

    def get_feature_names(self, columns: List[str]) -> Generator[str, None, None]:
        """
        Get feature names
        :param columns:
        :return:
        """
        for column in self.save_columns(columns):
            for variant in self.get_feature_variants(column):
                yield variant

    def get_feature_variants(self, column: str) -> Generator[str, None, None]:
        """
        Get feature variants
        :param column:
        :return:
        """
        yield f"moments:min({column})"
        yield f"moments:max({column})"
        yield f"moments:mean({column})"
        yield f"moments:min(abs({column}))"
        yield f"moments:max(abs({column}))"
        yield f"moments:mean(abs({column}))"
        yield f"moments:std({column})"

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {
            "inputs": self.get_variables(),
            "num_variants": len(list(self.get_feature_variants(""))),
            "outputs": {
                col: [
                    Variable(variant, "float")
                    for variant in self.get_feature_variants(col)
                ]
                for col in self.columns
            },
        }
