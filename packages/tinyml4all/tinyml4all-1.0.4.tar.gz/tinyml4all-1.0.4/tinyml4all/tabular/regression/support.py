import numpy as np


def reg_line(values: np.ndarray[float]) -> np.ndarray[float]:
    """
    Get regression line
    :param values:
    :return:
    """

    def reg_func(_x, _y):
        return np.linalg.pinv(_x).dot(_y)

    unique_values = sorted(np.unique(values))
    grid = np.linspace(np.min(unique_values), np.max(unique_values), len(unique_values))
    X, y = np.c_[np.ones(len(unique_values)), unique_values], unique_values
    grid = np.c_[np.ones(len(grid)), grid]

    return grid.dot(reg_func(X, y))
