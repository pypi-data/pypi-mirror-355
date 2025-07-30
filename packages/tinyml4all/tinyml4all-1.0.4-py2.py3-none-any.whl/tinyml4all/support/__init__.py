import inspect
import os
import webbrowser
from glob import glob, iglob
from pathlib import Path
from tempfile import gettempdir
from time import sleep
from typing import Union, Tuple, List, Any

import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas._libs.tslibs.parsing import DateParseError
from prettytable import PrettyTable
from sklearn.metrics import confusion_matrix

from tinyml4all.support.types import Array, cast
from tinyml4all.support.userwarn import userwarn


def slice_to_indices(
    s: Union[slice, Tuple[Union[None, int], Union[None, int]]], length: int
) -> List[int]:
    """
    Convert slice to list of indices
    :param s:
    :param length:
    :return:
    """
    if isinstance(s, Tuple):
        s = slice(*s)

    return list(range(*s.indices(length)))


def non_null(values: Array) -> Array:
    """
    Get non-null values in list
    :param values:
    :return:
    """
    return [x for x in values if x is not None]


def numeric(df: DataFrame, boolean: bool = False) -> DataFrame:
    """
    Get numeric columns of DataFrame
    :param df:
    :param boolean:
    :return:
    """
    return df.select_dtypes(
        include=["number", "bool"] if boolean else ["number"]
    ).astype(float)


def override(self: Any):
    """
    Mark function as to be overridden
    :return:
    """
    caller = inspect.stack()[1]
    function = caller.frame.f_code.co_name
    # allow self to be a static class, too
    self_type = self if type(self) == type else self.__class__

    raise NotImplementedError(f"{self_type.__name__}::{function}")


def pretty_confusion_matrix(
    y_true: Array, y_pred: Array, target_names: List[str]
) -> str:
    """
    Generate pretty ASCII confusion matrix
    :param y_true:
    :param y_pred:
    :param target_names:
    :return:
    """
    cf = confusion_matrix(y_true, y_pred)
    table = PrettyTable(["True vs Predicted"] + target_names)

    for target_name, row in zip(target_names, cf):
        table.add_row([target_name] + row.tolist())

    return str(table)


def view_html(convertible: "Convertible", **kwargs):
    """
    Render template as HTML and open in browser
    :param convertible:
    :param kwargs: additional template data
    :return:
    """
    html = convertible.convert_to("html", **kwargs)
    tmpname = os.path.join(gettempdir(), f"{abs(hash(html))}.html")

    with open(tmpname, "w") as f:
        f.write(html)

    webbrowser.open_new_tab(Path(f.name).as_uri())


def infer_timestamp_column(df: pd.DataFrame) -> str:
    """
    Infer timestamp column from data
    :param df:
    :return:
    """
    datetime_columns = infer_timestamp_columns(df)

    assert len(datetime_columns) > 0, "No datetime columns found in data"
    assert len(datetime_columns) == 1, (
        f"Multiple datetime columns found in data ({datetime_columns})"
    )

    return datetime_columns[0]


def infer_timestamp_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect all timestamp columns from data
    :param df:
    :return:
    """

    def is_datetime(value):
        try:
            return str(pd.Timestamp(value)) > "2000-01-01"
        except DateParseError:
            return False

    sample = df.sample(1).to_dict(orient="records")[0]
    return [col for col, value in sample.items() if is_datetime(value)]


def load_sources(folder: str, source_cls: type, **kwargs) -> List[Any]:
    """
    Load all sources from a folder
    :param folder:
    :param source_cls:
    :param kwargs:
    :return:
    """
    filenames = glob(os.path.join(folder, "*.csv"))

    return [
        source_cls.read_csv(filename, index=i, **kwargs)
        for i, filename in enumerate(filenames)
    ]


def not_self(locals: dict) -> dict:
    """
    Filter out self from locals
    :param locals:
    :return:
    """
    return {k: v for k, v in locals.items() if k != "self"}


def asset(path: str) -> str:
    """
    Get asset contents
    :param path:
    :return:
    """
    asset_path = os.path.join(
        os.path.dirname(__file__), "..", "transpile", "templates", "__assets__", path
    )

    return Path(asset_path).read_text()


def sample_indices(length: int, n: int) -> Array:
    """
    Sample indices from a list
    :param length:
    :param n:
    :return:
    """
    return np.unique(np.linspace(0, length - 1, n).astype(int))


def sample_values(arr: Array, n: int) -> np.ndarray[float]:
    """
    Sample values from an array
    :param arr:
    :param n:
    :return:
    """
    if len(arr) <= n:
        return np.asarray(arr)

    return np.asarray(arr)[sample_indices(len(arr), n)]


def get_frequency(timestamps: np.ndarray | pd.Series) -> int:
    """
    Get average frequency of timestamps
    :param timestamps:
    :return:
    """
    timestamps = np.asarray([t for t in timestamps])
    # sample 50 random timestamps
    indices = np.random.random_integers(1, len(timestamps) - 1, 50)
    # numpy timedelta is in nanoseconds
    shifts = [(timestamps[i] - timestamps[i - 1]).total_seconds() for i in indices]

    return int(1 / np.median(shifts))


def plain_filename(path: str) -> str:
    """
    Get plain filename from path
    :param path:
    :return:
    """
    return os.path.splitext(os.path.basename(path))[0]


def warn_or_raise(message: str, warn: bool):
    """
    Print warning or raise an error
    :param message:
    :param warn:
    :return:
    """
    if warn:
        userwarn(message)
    else:
        raise AssertionError(message)


def unpack_dict(d: dict, keys: str) -> List[Any]:
    """
    Unpack dict values
    :param d:
    :param keys:
    """
    return [[d[k] for k in keys.split(" ")]]


def confirm(prompt: str) -> bool:
    """
    Ask user confirmation
    :param prompt:
    :return:
    """
    return input(prompt.strip() + " [y|n] ").strip().lower().startswith("y")


def assert_folder(path: str):
    """
    Create folder if it does not exist
    :param path:
    :return:
    """
    path = cast(path, Path)

    assert not path.exists() or path.is_dir(), f"{path} exists, but is not a folder"

    if not path.exists() and confirm(f"Folder {path} does not exist: create?"):
        os.makedirs(str(path), 0o777)

    assert path.exists() and path.is_dir(), f"Folder {path} does not exist"


def ask_empty(path: str):
    """
    If a file exists, ask user to take its contents or wipe it
    :param path:
    :return:
    """
    if (
        not os.path.exists(path)
        or os.path.getsize(path) > 0
        and confirm(
            f"File {path} already exists and is not empty. Do you want to wipe its contents?"
        )
    ):
        with open(path, "w"):
            pass


def warn_non_empty(folder: str, globber: str):
    """
    Warn user if folder is not empty
    :param folder:
    :param globber:
    :return:
    """
    try:
        next(iglob(globber))
        userwarn(f"Folder {os.path.abspath(folder)} already contains {globber} files.")
    except StopIteration:
        pass


def countdown(count: int = 3):
    """
    Run a countdown.
    :return:
    """
    print("Task will start in ", end="")

    for i in range(count, 0, -1):
        print(f"{i}...", end="")
        sleep(1)

    print("START!")


def unique_ordered(values) -> List[Any]:
    """
    Get unique values while preserving order
    :param values:
    :return:
    """
    unique = []
    lookup = set([])

    for x in values:
        if x not in lookup:
            lookup.add(x)
            unique.append(x)

    return unique
