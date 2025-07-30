from typing import Dict, List

from tinyml4all.support import non_null


class HasClassmap:
    """
    Mixin for classes that have a classmap
    """

    @property
    def unique_labels(self) -> List[str]:
        """
        Get unique labels
        :return:
        """
        labels = sorted(non_null(set(self.Y_true)))

        # in case of binary classification (class vs not class)
        # ensure that not(class) is always the first (a.k.a. 0)
        if len(labels) == 2 and any(label.startswith("not(") for label in labels):
            negative = next(label for label in labels if label.startswith("not("))
            labels = [negative] + [
                label for label in labels if not label.startswith("not(")
            ]

        return labels

    @property
    def classmap(self) -> Dict[str, int]:
        """
        Get mapping from label to index
        :return:
        """
        return {str(y): i for i, y in enumerate(self.unique_labels)}

    @property
    def inverse_classmap(self) -> Dict[int, str]:
        """
        Get mapping from label to index
        :return:
        """
        return {i: str(y) for i, y in enumerate(self.unique_labels)}
