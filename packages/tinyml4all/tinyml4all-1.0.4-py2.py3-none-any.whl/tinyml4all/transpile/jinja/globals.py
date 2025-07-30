import numpy as np

from tinyml4all.support import asset
from tinyml4all.support.types import Array
from tinyml4all.transpile.jinja.filters import to_c_array


def get_globals(language: str) -> dict:
    """
    Get globals for Jinja2 templates
    """
    # common globals
    globals = {
        "id": id,
        "np": np,
        "len": len,
        "zip": zip,
        "int": int,
        "str": str,
        "iter": iter,
        "next": next,
        "ceil": np.ceil,
        "eps": 0.0001,
        "floor": np.floor,
        "range": range,
        "asset": asset,
        "sorted": sorted,
        "enumerate": enumerate,
        "isinstance": isinstance,
        "FLOAT_MAX": "3.402823466e+38F",
        "FLOAT_MIN": "-3.402823466e+38F",
    }

    # language-specific globals
    match language:
        case "c++":
            globals.update({"define_array": define_c_array})

    return globals


def define_c_array(
    var_name: str, arr: Array, precision: int = 6, semicolon: bool = False
) -> str:
    """
    Generate C array definition
    :param var_name:
    :param arr:
    :param precision:
    :param semicolon:
    :return:
    """
    if not hasattr(arr, "shape"):
        arr = np.asarray(arr)

    shape = "][".join(str(x) for x in arr.shape)
    semicolon = ";" if semicolon else ""

    return f"{var_name}[{shape}] = {to_c_array(arr, precision)}" + semicolon
