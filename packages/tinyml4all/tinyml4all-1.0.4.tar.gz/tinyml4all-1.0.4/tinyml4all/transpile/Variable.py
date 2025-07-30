import numpy as np
from tinyml4all.transpile.Jsonable import Jsonable


class Variable(Jsonable):
    """
    Variable wrapper for Inputs
    """

    def __init__(self, name: str, dtype: str):
        """
        Constructor
        :param name:
        :param dtype:
        """
        self.name = name
        self.dtype = float if np.issubdtype(dtype, np.number) else str

    def __eq__(self, other):
        """
        Compare variables
        :param other:
        :return:
        """
        return hash(self) == hash(other)

    def __hash__(self):
        """
        Get unique hash
        :return:
        """
        return hash((self.name, self.dtype))

    def __repr__(self):
        """
        Convert to string
        :return:
        """
        return f"({self.name}: {self.dtype})"

    @property
    def is_numeric(self) -> bool:
        """
        Test if variable is numeric
        :return:
        """
        return self.dtype == float

    @property
    def is_reserved(self):
        """
        Test if variable is reserved
        :return:
        """
        return self.name.startswith("__")

    def c_type(self) -> str:
        """
        Get type for C/C++
        :return:
        """
        return "float" if self.dtype == float else "const char *"

    def to_json(self) -> dict:
        """
        Convert to JSON
        :return:
        """
        return {"name": self.name, "dtype": "float" if self.is_numeric else "str"}
