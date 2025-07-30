from typing import List, Any, Self

from tinyml4all.support import userwarn
from tinyml4all.support.types import coalesce, TemplateDef
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock
from tinyml4all.time.continuous.classification.ContinuousClassificationTimeSeries import (
    ContinuousClassificationTimeSeries,
)
from tinyml4all.time.continuous.features.Window import Window as ContinuousWindow
from tinyml4all.time.continuous.classification import Chain as ContinuousChain
from tinyml4all.time.episodic.classification.BinaryChain import BinaryChain
from tinyml4all.time.episodic.classification.BinaryDataset import BinaryDataset
from tinyml4all.time.episodic.classification.EpisodicClassificationTimeSeries import (
    EpisodicClassificationTimeSeries,
)
from tinyml4all.time.episodic.features import Window
from tinyml4all.time.continuous.classification import Chain as Base
from tinyml4all.transpile.Variables import Variables
from tinyml4all.tabular.classification import Chain as TabularChain


class Chain(Base):
    """
    Episodic time series classification chain
    """

    def __init__(
        self,
        *,
        window: Window,
        ovr: List[ProcessingBlock],
        pre: List[ProcessingBlock] = None,
    ):
        """
        Constructor
        :param window:
        :param ovr:
        :param pre:
        """
        Base.__init__(self)

        self.pre = TabularChain(*pre) if pre else None
        self.window = window
        self.ovr = ovr
        self.chains: List[ContinuousChain] = []

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {
            "variables": Variables(
                [block for chain in self.chains for block in chain.blocks]
            ),
            "pre": self.pre,
            "window": sorted(
                [chain.get_block_of_type(ContinuousWindow) for chain in self.chains],
                key=lambda window: window.length,
            )[-1],
            "ovr": self.chains,
            "classmap": self.classmap,
        }

    def fit(
        self, dataset: EpisodicClassificationTimeSeries, *args, **kwargs
    ) -> List[ContinuousClassificationTimeSeries]:
        """
        Fit binary versions of the dataset
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        self.unfit()

        tables = []
        self.chains = []

        # fit pre chain, if any
        if self.pre is not None:
            dataset = self.pre(dataset)

        self.assert_durations_are_set(dataset)

        for i, label in enumerate(dataset.unique_labels):
            # convert episodic to binary continuous
            binary_dataset = BinaryDataset.convert(dataset, label=label)
            duration = dataset.event_durations[label]
            half = duration / 2

            # todo: improve performance
            for t in binary_dataset.event_timestamps:
                start_at = t - half - self.window.shift
                end_at = t + half + self.window.shift
                binary_dataset.add_label(label, start_at, end_at)

            # create continuous chain
            window = ContinuousWindow(
                length=duration, shift=self.window.shift, features=self.window.features
            )
            binary_chain = BinaryChain(label, *([window] + list(self.ovr)))

            table = binary_chain(binary_dataset)
            tables.append(table)
            self.chains.append(binary_chain)

        self.fitted = True

        return tables

    def transform(
        self, dataset: EpisodicClassificationTimeSeries, *args, **kwargs
    ) -> Any:
        """
        Transform dataset
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        results = []

        # transform pre chain, if any
        if self.pre is not None:
            dataset = self.pre(dataset)

        for chain in self.chains:
            binary_dataset = BinaryDataset.convert(dataset, label=chain.label)
            duration = dataset.event_durations[chain.label]
            half = duration / 2

            for t in binary_dataset.event_timestamps:
                start_at = t - half - self.window.shift
                end_at = t + half + self.window.shift
                binary_dataset.add_label(chain.label, start_at, end_at)

            results.append(chain(binary_dataset))

        return results

    def unfit(self) -> Self:
        """
        Unfit chains
        :return:
        """
        if self.pre is not None:
            self.pre.unfit()

        for chain in self.chains:
            chain.unfit()

        self.fitted = False

        return self

    def assert_durations_are_set(self, dataset: EpisodicClassificationTimeSeries):
        """
        Assert that durations are set
        :return:
        """
        for i, label in enumerate(dataset.unique_labels):
            if label not in dataset.event_durations:
                userwarn(
                    f"Label {label} doesn't have a duration set. I'll default to 1 second, but you should really set one with ts.set_duration(label, duration)"
                )
                dataset.set_duration(label, "1s")
