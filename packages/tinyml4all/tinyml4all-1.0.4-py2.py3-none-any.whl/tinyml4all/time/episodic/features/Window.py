from typing import List

import pandas as pd

from tinyml4all.support.types import cast


class Window:
    """
    Chunk data into windows.
    Different from time.continuous.Window, this window
    doesn't have a duration, because it is label-dependant!
    """

    def __init__(
        self,
        features: List[callable],
        chunk: str | pd.Timedelta = None,
        shift: str | pd.Timedelta = None,
    ):
        """
        Constructor
        :param features:
        :param chunk:
        :param shift:
        """
        assert chunk is not None or shift is not None, (
            "Either chunk or shift must be set"
        )

        self.features = features
        self.chunk = cast(chunk, pd.Timedelta) if chunk is not None else None
        self.shift = cast(shift or chunk, pd.Timedelta)
