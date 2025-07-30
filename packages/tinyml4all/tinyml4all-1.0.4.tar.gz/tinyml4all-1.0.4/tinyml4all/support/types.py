import importlib
from typing import List, Any, Union, Iterable, Callable, Tuple, Set

import numpy as np
import pandas as pd
from numpy import ndarray
from pandas import Series

Array = Union[None, Set[Any], List[Any], ndarray, Series]
ArrayOfStrings = Union[str, List[str]]
TemplateName = str
TemplateData = dict
TemplateDef = Union[TemplateData, Tuple[TemplateName, TemplateData]]


def cast(value: Any, type_: type, caster: Callable = None) -> Any:
    """
    Cast value to type
    :param value:
    :param type_:
    :param caster:
    :return:
    """
    if value is None:
        return None

    if isinstance(value, type_):
        return value

    return type_(value) if caster is None else caster(value)


def coalesce(value: Any, default: Union[callable, Any]) -> Any:
    """
    Coalesce value
    :param value:
    :param default:
    :return:
    """
    if value is not None:
        return value

    if callable(default):
        default = default()

    return default


def is_iterable(value: Any, dtype: Union[type, Callable[[Any], bool]] = None) -> bool:
    """
    Check if value is array-like
    :param value:
    :param dtype:
    :return:
    """
    if (
        isinstance(value, list)
        or isinstance(value, np.ndarray)
        or isinstance(value, pd.Series)
    ):
        # check type, if specified
        if dtype is None:
            return True

        if isinstance(dtype, type):
            return all(isinstance(x, dtype) for x in value)

        return all(dtype(x) for x in value)

    return False


def as_list_of_strings(
    value: ArrayOfStrings | None, sep: str = ","
) -> List[str] | None:
    """
    Convert comma-separated string into a list
    :param value:
    :param sep:
    :return:
    """
    if value is None:
        return None

    if isinstance(value, str):
        return [s.strip() for s in value.split(sep) if s.strip()]

    return value


def hydrate(definition: dict) -> Any:
    """
    Hydrate object from definition
    :param definition:
    :return:
    """
    assert "__type__" in definition, "Classname not found"

    fqcn = definition.pop("__type__")
    module_name, class_name = fqcn.rsplit(".", 1)
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)

    return cls(**definition)
