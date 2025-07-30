import seaborn as sns

from typing import Tuple, List

from tinyml4all.support.types import coalesce


def to_hex_color(color: Tuple[float, float, float], opacity: float = 1) -> str:
    """
    Convert RGB tuple to hex color
    :param color:
    :param opacity:
    :return:
    """
    return "#{:02x}{:02x}{:02x}".format(
        *[int(255 * c) for c in color]
    ) + "{:02x}".format(int(255 * opacity))


def to_rgba_color(color: Tuple[float, float, float], opacity: float = 1) -> str:
    """
    Convert RGB tuple to rgba color
    :param color:
    :param opacity:
    :return:
    """
    return f"rgba({', '.join([str(int(c * 255)) for c in color])}, {opacity})"


def hex_colors(palette: str, n_colors: int, opacity: float = 1) -> List[str]:
    """
    Get list of hex colors
    :param palette:
    :param n_colors:
    :param opacity:
    :return:
    """
    return [
        to_hex_color(color, opacity=opacity)
        for color in sns.color_palette(coalesce(palette, "viridis"), n_colors=n_colors)
    ]


def rgba_colors(palette: str, n_colors: int, opacity: float = 1) -> List[str]:
    """
    Get list of rgba colors
    :param palette:
    :param n_colors:
    :param opacity:
    :return:
    """
    return [
        to_rgba_color(color, opacity=opacity)
        for color in sns.color_palette(coalesce(palette, "viridis"), n_colors=n_colors)
    ]
