from typing import Self, Any, List

from tinyml4all.support.types import TemplateDef, hydrate
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock
from tinyml4all.transpile.Convertible import Convertible
from tinyml4all.transpile.Variables import Variables


class Chain(Convertible):
    """
    A list of blocks
    """

    @staticmethod
    def hydrate(blocks: List[dict]) -> "Chain":
        """
        Hydrate chain from block objects
        :param blocks:
        :return:
        """
        blocks = [hydrate(block) for block in blocks]

        return Chain(*blocks)

    def __init__(self, *blocks):
        """
        Constructor
        """
        self.blocks = list(blocks)
        self.fitted = False
        self.classmap = None

    def __str__(self):
        """
        Get string representation
        :return:
        """
        return f"Chain(blocks={self.blocks})"

    def __repr__(self):
        """
        Get string representation
        :return:
        """
        return str(self)

    def __call__(self, dataset, *args, **kwargs):
        """
        Fit transform
        :param dataset:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.fitted:
            return self.fit(dataset, *args, **kwargs)

        return self.transform(dataset, *args, **kwargs)

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {
            "blocks": self.blocks,
            "variables": Variables(self.blocks),
            "classmap": self.classmap,
        }

    def unfit(self) -> Self:
        """
        Unfit all blocks
        :return:
        """
        [block.unfit() for block in self.blocks]
        self.fitted = False

        return self

    def fit(self, dataset: Any, *args, **kwargs) -> Any:
        """
        Fit blocks
        :param dataset:
        :return:
        """
        self.unfit()

        self.classmap = getattr(dataset, "classmap", self.classmap)

        # make a forward pass to configure blocks
        for index, block in enumerate(self.blocks):
            block.configure_from(dataset, blocks=self.blocks, index=index)

        for block in self.blocks:
            dataset = block(dataset, *args, **kwargs)

        self.fitted = True

        return dataset

    def transform(self, dataset: Any, *args, **kwargs) -> Any:
        """
        Apply transformers
        :param dataset:
        :return:
        """
        for block in self.blocks:
            dataset = block(dataset, *args, **kwargs)

        return dataset

    def get_block_of_type(self, dtype: type) -> ProcessingBlock:
        """
        Get block of type
        :param dtype:
        :return:
        """
        return next(block for block in self.blocks if isinstance(block, dtype))
