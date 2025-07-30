from typing import List

import numpy as np
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report

from tinyml4all.support import pretty_confusion_matrix, unique_ordered
from tinyml4all.support.types import coalesce


class Report:
    """
    Results report
    """

    def __init__(self):
        """
        Constructor
        """
        self.history: dict = {}
        self.ground_truth = None
        self.pred = None
        self.unique_labels = None

    def set_history(self, history: "keras.src.callbacks.History"):
        """
        Set history
        :param history:
        :return:
        """
        self.history = history.history

    def set_results(self, ground_truth: np.ndarray, pred: np.ndarray):
        """
        Set results
        :param ground_truth:
        :param pred:
        :return:
        """
        self.ground_truth = ground_truth
        self.pred = pred

    def set_target_names(self, target_names: List[str]):
        """
        Set target names
        :param target_names:
        :return:
        """
        self.unique_labels = target_names

    def plot(self):
        """
        Plot history
        :return:
        """
        if "val_categorical_accuracy" in self.history:
            metric = "val_categorical_accuracy"

        plt.figure()
        plt.plot(np.clip(self.history["loss"], 0, 1), label="Loss")
        plt.plot(self.history[metric], label=metric)
        plt.plot(np.ones_like(self.history["loss"]), "r--", label="Perfection")
        plt.title("Model history")
        plt.xlabel("Epoch")
        plt.legend(loc="upper left")
        plt.show()

    def classification_report(self) -> str:
        """
        Get classification report
        :return:
        """
        pred = self.pred.argmax(axis=1).astype(int)
        ground_truth = self.ground_truth.argmax(axis=1).astype(int)

        Y_pred = [y for y in pred if y is not None]
        Y_true = [y for y, pred in zip(ground_truth, pred) if pred is not None]
        target_names = coalesce(
            self.unique_labels, [f"Label-{i}" for i in unique_ordered(Y_true)]
        )

        print(
            "\n".join(
                [
                    classification_report(
                        Y_true,
                        Y_pred,
                        target_names=target_names,
                        zero_division=np.nan,
                    ),
                    pretty_confusion_matrix(
                        Y_true,
                        Y_pred,
                        target_names=target_names,
                    ),
                ]
            )
        )
