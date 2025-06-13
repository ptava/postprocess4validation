from functools import lru_cache
from numpy import ndarray, zeros
from matplotlib.colors import hsv_to_rgb
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter
from pathlib import Path

from .utils import logger


@lru_cache(maxsize=32)
def get_distinct_color(index: int, h_start: float = 0.5) -> ndarray:
    """
    Generate a distinct RGB color based on the golden ratio.

    Parameters
    ----------
    index (int): index to determine the color in the sequence
    h_start : float(optional): starting hue value, by default 0.5

    Returns
    -------
    numpy ndarray indicating RGB color
    """
    number = 0.618033  # Golden ratio
    h = (h_start + index * number) % 1.0
    s = 0.65
    v = 0.95
    try:
        set_color = hsv_to_rgb((h, s, v))
    except Exception as e:
        logger.error(f"Error converting HSV to RGB: {e}")
        set_color = zeros(3, dtype=float)
    return set_color


def get_marker(index: int) -> str:
    """
    Return a marker from a list of markers, cycling through them as index grows.

    Parameters
    ----------
    index (int): index to determine the marker in the sequence

    Returns
    -------
    str: Matplotlib marker symbol
    """
    markers = [
        "x", "s", "^", "*", "p", "d", "h",
        "v", ">", "<", "1", "2", "3", "4"
    ]
    return markers[index % len(markers)]


def connect_save_event(fig: Figure, plot_file: Path) -> None:
    """
    Connect the save event to the figure canvas.

    Parameters
    ----------
    fig (matplotlib.figure.Figure): The figure object to connect the save event to.
    plot_file (Path): The path to the file where the plot will be saved.

    """
    fig.canvas.mpl_connect(
        'close_event',
        lambda event: fig.savefig(plot_file)
    )


class CustomFormatStrFormatter(FormatStrFormatter):
    """
    Custom formatter for axis tick labels that displays integers without decimal points
    and floats with one decimal place.
    """

    def __call__(self, x, pos=None):
        """
        Format the tick value based on whether it's an integer or float.

        Parameters
        ----------
        x (float): the tick value to format
        pos (int, optional): the tick position, by default None

        """
        if x.is_integer():
            return f'{x:.0f}'
        else:
            return f'{x:.1f}'
