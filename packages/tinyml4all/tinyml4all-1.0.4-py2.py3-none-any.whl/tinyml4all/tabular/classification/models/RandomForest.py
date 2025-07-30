from copy import deepcopy

from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from tinyml4all.support.types import TemplateDef, cast
from tinyml4all.tabular.classification.models.DecisionTree import DecisionTree
from tinyml4all.tabular.classification.models.Estimator import Estimator


class RandomForest(Estimator):
    """
    Proxy to sklearn.ensemble.RandomForestClassifier
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

        self.estimator = RandomForestClassifier(
            n_estimators=cast(n_estimators, int),
            max_depth=cast(max_depth, int),
            min_samples_leaf=cast(min_samples_leaf, int),
            **kwargs,
        )

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """

        def wrap(tree: DecisionTreeClassifier):
            wrapped = DecisionTree()
            wrapped.estimator = tree
            wrapped.input_dtypes = self.input_dtypes
            wrapped.working_dtypes = self.working_dtypes

            return wrapped

        return {
            "num_classes": len(self.estimator.classes_),
            "trees": [wrap(deepcopy(tree)) for tree in self.estimator.estimators_],
        }

    @staticmethod
    def __help__():
        """
        Get help
        :return:
        """
        return """
            Parameters
            ----------
            n_estimators : int, default=15
                The number of trees in the forest.

            criterion : {"gini", "entropy", "log_loss"}, default="gini"
                The function to measure the quality of a split. Supported criteria are
                "gini" for the Gini impurity and "log_loss" and "entropy" both for the
                Shannon information gain, see :ref:`tree_mathematical_formulation`.
                Note: This parameter is tree-specific.

            max_depth : int, default=10
                The maximum depth of the tree. If None, then nodes are expanded until
                all leaves are pure or until all leaves contain less than
                min_samples_split samples.

            min_samples_split : int or float, default=2
                The minimum number of samples required to split an internal node:

                - If int, then consider `min_samples_split` as the minimum number.
                - If float, then `min_samples_split` is a fraction and
                  `ceil(min_samples_split * n_samples)` are the minimum
                  number of samples for each split.

            min_samples_leaf : int or float, default=5
                The minimum number of samples required to be at a leaf node.
                A split point at any depth will only be considered if it leaves at
                least ``min_samples_leaf`` training samples in each of the left and
                right branches.  This may have the effect of smoothing the model,
                especially in regression.

                - If int, then consider `min_samples_leaf` as the minimum number.
                - If float, then `min_samples_leaf` is a fraction and
                  `ceil(min_samples_leaf * n_samples)` are the minimum
                  number of samples for each node.

            min_weight_fraction_leaf : float, default=0.0
                The minimum weighted fraction of the sum total of weights (of all
                the input samples) required to be at a leaf node. Samples have
                equal weight when sample_weight is not provided.

            max_features : {"sqrt", "log2", None}, int or float, default="sqrt"
                The number of features to consider when looking for the best split:

                - If int, then consider `max_features` features at each split.
                - If float, then `max_features` is a fraction and
                  `max(1, int(max_features * n_features_in_))` features are considered at each
                  split.
                - If "sqrt", then `max_features=sqrt(n_features)`.
                - If "log2", then `max_features=log2(n_features)`.
                - If None, then `max_features=n_features`.

                Note: the search for a split does not stop until at least one
                valid partition of the node samples is found, even if it requires to
                effectively inspect more than ``max_features`` features.

            max_leaf_nodes : int, default=None
                Grow trees with ``max_leaf_nodes`` in best-first fashion.
                Best nodes are defined as relative reduction in impurity.
                If None then unlimited number of leaf nodes.

            min_impurity_decrease : float, default=0.0
                A node will be split if this split induces a decrease of the impurity
                greater than or equal to this value.

                The weighted impurity decrease equation is the following::

                    N_t / N * (impurity - N_t_R / N_t * right_impurity
                                        - N_t_L / N_t * left_impurity)

                where ``N`` is the total number of samples, ``N_t`` is the number of
                samples at the current node, ``N_t_L`` is the number of samples in the
                left child, and ``N_t_R`` is the number of samples in the right child.

                ``N``, ``N_t``, ``N_t_R`` and ``N_t_L`` all refer to the weighted sum,
                if ``sample_weight`` is passed.

                class_weight : {"balanced", "balanced_subsample"}, dict or list of dicts, default=None
                Weights associated with classes in the form ``{class_label: weight}``.
                If not given, all classes are supposed to have weight one. For
                multi-output problems, a list of dicts can be provided in the same
                order as the columns of y.

                Note that for multioutput (including multilabel) weights should be
                defined for each class of every column in its own dict. For example,
                for four-class multilabel classification weights should be
                [{0: 1, 1: 1}, {0: 1, 1: 5}, {0: 1, 1: 1}, {0: 1, 1: 1}] instead of
                [{1:1}, {2:5}, {3:1}, {4:1}].

                The "balanced" mode uses the values of y to automatically adjust
                weights inversely proportional to class frequencies in the input data
                as ``n_samples / (n_classes * np.bincount(y))``

                The "balanced_subsample" mode is the same as "balanced" except that
                weights are computed based on the bootstrap sample for every tree
                grown.

                For multi-output, the weights of each column of y will be multiplied.

                Note that these weights will be multiplied with sample_weight (passed
                through the fit method) if sample_weight is specified.

                max_samples : int or float, default=None
                If bootstrap is True, the number of samples to draw from X
                to train each base estimator.

                - If None (default), then draw `X.shape[0]` samples.
                - If int, then draw `max_samples` samples.
                - If float, then draw `max(round(n_samples * max_samples), 1)` samples. Thus,
                  `max_samples` should be in the interval `(0.0, 1.0]`.
            """
