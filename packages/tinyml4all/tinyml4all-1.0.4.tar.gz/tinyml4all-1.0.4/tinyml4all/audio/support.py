import re


def parse_freq(freq: str) -> int:
    """
    Parse frequency
    :param freq:
    :return:
    """
    return int(re.sub(r"\D", "", freq.replace("k", "000")))
