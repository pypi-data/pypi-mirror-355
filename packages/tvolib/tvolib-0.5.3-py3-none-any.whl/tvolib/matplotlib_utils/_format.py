__all__ = [
    "add_colorbar",
    "add_panel_label",
    "format_datetime_labels",
]

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable


def add_colorbar(
    ax: plt.Axes,
    where: str = "right",
    pad: float = 0.05,
    size: str = "2%",
) -> plt.Axes:
    r"""
    Adds colorbar next to a given `Axes` instance. See `matplotlib`
    documentation for `where`, `pad`, and `size` options.

    Parameters
    ----------
    ax: `matplotlib.axes.Axes`
        The `Axes` instance to draw on.
    where: str
        Where to append the colorbar with respective to the `Axes`.
    pad: str
        Padding of the colorbar from the `Axes`.
    size: str
        Size of the colorbar relative to the `Axes`.

    Return
    ------
    cax: `matplotlib.axes.Axes`
        A child `Axes` instance created relative to the input `Axes` for
        drawing the colorbar.
    """
    divider = make_axes_locatable(ax)
    return divider.append_axes(where, size=size, pad=pad)


def add_panel_label(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    box_format: dict = dict(facecolor="wheat", alpha=0.9),
    **kwargs,
) -> None:
    r"""
    Adds a boxed text to an `Axes` instance. Intended for drawing panel
    annotations for a figure.

    Parameters
    ----------
    ax: `matplotlib.axes.Axes`
        The `Axes` instance to draw on.
    x, y: float
        Location of the text.
    text: str
        Content of the the text.
    box_format: dict
        Formatting of the enclosing box.
    kwargs: dict
        Other options for `Axes.text` method.
    """
    ax.text(x, y, text, transform=ax.transAxes, bbox=box_format, **kwargs)


def format_datetime_labels(ax: plt.Axes) -> None:
    r"""
    Format the labels for plots with `numpy.datetime64` abscissa.

    Parameter
    ---------
    ax: `matplotlib.axes.Axes`
        The `Axes` instance.
    """
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_formatter(formatter)
