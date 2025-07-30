import json
import re
from typing import Any

import numpy as np

from tinyml4all.transpile.jinja.JsExpr import JsExpr


class JSONEncoder(json.JSONEncoder):
    """
    JSON encoder that can handle datetime objects and numpy arrays
    """

    def default(self, o):
        if isinstance(o, JsExpr):
            return o.expr
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if hasattr(o, "to_numpy"):
            return o.to_numpy().tolist()
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.int64):
            return int(o)
        return super().default(o)

    def encode(self, o) -> str:
        """
        Encode object
        :param o:
        :return:
        """
        encoded = super().encode(o)

        # evaluate js expressions
        encoded = re.sub(
            r'"(\([^)]*\) => ([\s\S]+?))",', lambda m: m.group(1) + ",", encoded
        )

        return encoded

    def eval(self, value: Any) -> Any:
        """
        Encode/Decode
        :param value:
        :return:
        """
        return json.loads(self.encode(value))
