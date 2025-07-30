from copy import deepcopy
from typing import List

from tinyml4all.support.types import TemplateDef
from tinyml4all.tabular.ProcessingBlock import ProcessingBlock
from tinyml4all.time.continuous.classification import Chain
from tinyml4all.time.continuous.features import Window


class BinaryChain(Chain):
    """
    Episodic classification chain on binary data
    """

    def __init__(self, label: str, *blocks):
        """
        Constructor
        """
        super().__init__(*[deepcopy(block) for block in blocks])
        self.label = label

    @property
    def ovr_blocks(self) -> List[ProcessingBlock]:
        """
        Get blocks after the window (included)
        :return:
        """
        window_index = next(
            i for i, block in enumerate(self.blocks) if isinstance(block, Window)
        )

        return self.blocks[window_index + 1 :]

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return {
            "blocks": self.ovr_blocks,
            "window": next(block for block in self.blocks if isinstance(block, Window)),
        }
