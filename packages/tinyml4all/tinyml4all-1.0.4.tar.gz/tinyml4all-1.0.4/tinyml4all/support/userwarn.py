import warnings


def userwarn(message: str):
    """
    Print warning without source line
    :param message:
    :return:
    """
    warnings.warn(message, stacklevel=100)
