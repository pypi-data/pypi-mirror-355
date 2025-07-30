import base64
import hashlib
import json
import re
from typing import Any, Iterable, List

import numpy as np
from numpy import ceil, floor

from tinyml4all.support.types import Array
from tinyml4all.transpile.Variable import Variable
from tinyml4all.transpile.jinja.JSONEncoder import JSONEncoder


def get_filters(language: str) -> dict:
    """
    Get filters for given language
    :param language:
    :return:
    """
    # common filters
    filters = {
        "ceil": ceil,
        "floor": floor,
        "var": to_var_name,
        "to_json": lambda x: json.dumps(x, cls=JSONEncoder, indent=2),
    }

    # language-specific filters
    match language:
        case "c++":
            filters.update(
                {
                    "spread": spread,
                    "to_array": to_c_array,
                    "to_shape": to_c_shape,
                    "to_input_array": to_input_array,
                    "spread_signature": spread_signature,
                }
            )

    return filters


def spread(variables: List[Variable], pointer: bool = False, object: str = None) -> str:
    """
    Spread variables
    :param variables:
    :param pointer:
    :param object:
    :return:
    """
    names = [to_var_name(var) for var in variables]

    if object:
        names = [f"{object}{name}" for name in names]

    if pointer:
        names = [f"&({name})" for name in names]

    return ", ".join(names)


def spread_signature(
    variables: List[Variable], pointer: bool = False, const: bool = False
) -> str:
    """
    Spread variables
    :param variables:
    :param pointer:
    :param const:
    :return:
    """
    const = "const " if const else ""
    pointer = "*" if pointer else ""

    return ", ".join(
        f"{const}{var.c_type()}{pointer} {to_var_name(var.name)}" for var in variables
    )


def to_var_name(name: Any) -> str:
    """
    Transform name to valid variable name
    :param name:
    :return:
    """
    # if object is passed, get its name attribute
    name = getattr(name, "name", name)

    # if still not a string, assume it is an object
    # so get its class name + id
    if type(name) != str:
        name = f"{name.__class__.__name__}_{id(name)}_{hash(name)}"

    s = hashlib.md5(name.encode()).digest()
    b = base64.b64encode(s).decode()
    short_hash = re.sub(r"\W", "", b)[:6]

    return "_" + short_hash + "__" + re.sub(r"[^\w\d_]", "", name.lower())


def to_c_array(arr: Array | float, precision: int = 6) -> str:
    """
    Convert array to C format
    :param arr:
    :param precision:
    :return:
    """
    if isinstance(arr, str):
        return '"%s"' % arr

    if not isinstance(arr, Iterable):
        return str(round(arr, precision))

    return "{%s}" % (", ".join([to_c_array(x, precision) for x in arr]))


def to_c_shape(shape) -> str:
    """
    Convert shape to C format
    :param shape:
    :return:
    """
    if isinstance(shape, np.ndarray):
        return to_c_shape(shape.shape)

    return "][".join(str(s) for s in shape)


def to_input_array(vars: List[Variable]) -> str:
    """
    Convert array to C format
    :param vars:
    :return:
    """
    names = ["input.%s" % to_var_name(var) for var in vars]

    return "{" + ", ".join(names) + "}"
