from typing import Any, List, Set

from tinyml4all.transpile.Variable import Variable


class Variables:
    """
    Handle many Variables
    """

    # todo: type hint ProcessingBlock
    def __init__(self, blocks: List[Any]):
        """
        Constructor
        :param blocks:
        """
        self.blocks = blocks

    @property
    def inputs(self) -> List[Variable]:
        """
        Get input variables
        :return:
        """
        return [var for var in self.blocks[0].input_dtypes if not var.is_reserved]

    @property
    def all(self) -> Set[Variable]:
        """
        Get all variables, in no particular order
        :return:
        """
        return set(
            [
                var
                for block in self.blocks
                for var in block.input_dtypes
                if not var.is_reserved
            ]
            + [var for block in self.blocks for var in block.output_dtypes]
        )
