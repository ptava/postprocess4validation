from numpy import zeros, uint8, asarray
from matplotlib.ticker import MultipleLocator
import matplotlib.transforms as mtransforms
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import mark_inset, inset_axes
from typing import Tuple, Dict, Any

from ..core import CustomFormatStrFormatter


def add_interactive_lens(
    fig,
    ax,
    delta_log: float = 0.1,
    inset_size: str = "70%",
    lens_box: Tuple[float, float, float, float] = (0.05, 0.37, 0.6, 0.6)
) -> None:
    """
    Add an interactive, fixed-size "lens" (inset Axes) to an existing log-log Axes.

    This lens will show a magnified view around the mouse pointer on the main Axes
    when the lens is toggled on. Press the space bar to toggle the lens.

    Parameters
    ----------
    fig (matplotlib.figure.Figure): the Matplotlib Figure containing `ax`.
    ax (matplotlib.axes.Axes): the main Axes object on which to add the lens.
    delta_log (float, optional): the constant delta in log10 space used to
        define the width/height of the lens in log-scaled axes. Default is 0.1.
    inset_size (str, optional): the size of the lens inset as a percentage of
        the main Axes. Default is "70%".
    lens_box (tuple of float, optional): bounding box (left, bottom, width, 
        height) for the lens in Axes-relative coordinates. Default is (0.05,
        0.37, 0.6, 0.6).

    Notes
    -----
    - Press the space bar to toggle the lens on or off.
    - When the lens is active, moving the mouse in the main Axes updates the lens
      region around the pointer.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> # Create your plot on ax
    >>> add_interactive_lens(fig, ax)
    >>> plt.show()
    """
    # Validate inputs
    if not isinstance(fig, Figure):
        raise TypeError("fig must be a matplotlib Figure")
    if not isinstance(ax, Axes):
        raise TypeError("ax must be a matplotlib Axes")
    if not isinstance(delta_log, (int, float)) or delta_log <= 0:
        raise ValueError("delta_log must be a positive number")

    # Create an inset axis (the "lens") with fixed size relative to ax.
    lens_ax = inset_axes(
        ax,
        width=inset_size,
        height=inset_size,
        bbox_to_anchor=lens_box,
        bbox_transform=ax.transAxes,
        loc="upper left",
    )

    # Create a placeholder image on the lens; its content will be updated.
    placeholder = zeros((10, 10, 3), dtype=uint8)
    lens_im = lens_ax.imshow(
        placeholder,
        interpolation="nearest",
        aspect="auto",
        extent=[1, 2, 1, 2],
    )

    # Match the scales of the main Axes.
    lens_ax.set_xscale(ax.get_xscale())
    lens_ax.set_yscale(ax.get_yscale())
    lens_ax.set_visible(False)  # start hidden

    # Dictionary to hold whether the lens is active and the "mark_inset" handle.
    lens_state = {
        "active": False,
        "mark_inset_handle": None,
    }

    # Connect the event handlers to the figure
    fig.canvas.mpl_connect(
        "key_press_event",
        lambda event: _on_key_press(
            event, fig, ax, lens_ax, lens_state
        ),
    )
    fig.canvas.mpl_connect(
        "motion_notify_event",
        lambda event: _on_mouse_move(
            event, fig, ax, lens_ax, lens_im, lens_state, delta_log
        ),
    )


def _on_key_press(
    event: Any,
    fig: Figure,
    ax: Axes,
    lens_ax: Axes,
    lens_state: Dict[str, Any],
) -> None:
    """
    Handle key press events to toggle the lens when the space bar is pressed.

    Parameters
    ----------
    event : matplotlib event
        The key press event
    fig (matplotlib.figure.Figure): the figure containing the axes
    ax : matplotlib.axe(Axes): the main axes
    lens_ax : matplotlib.axe(Axes): the lens axes
    lens_im : matplotlib.imag(AxesImage): the image in the lens
    lens_state (dict): dictionary tracking the lens state
    delta_log (float): the delta in log10 space for the lens
    """
    if event.key == " ":
        lens_state["active"] = not lens_state["active"]
        lens_ax.set_visible(lens_state["active"])

        # If the lens is toggled on, add the inset marker if not present.
        if lens_state["active"]:
            if lens_state["mark_inset_handle"] is None:
                lens_state["mark_inset_handle"] = mark_inset(
                    ax,
                    lens_ax,
                    loc1=1,
                    loc2=3,
                    ec="gray",
                    lw=0.5,
                )
            # Example usage of the custom formatter:
            lens_ax.xaxis.set_major_formatter(CustomFormatStrFormatter(""))
            lens_ax.yaxis.set_major_formatter(CustomFormatStrFormatter(""))
            lens_ax.xaxis.set_minor_formatter(CustomFormatStrFormatter(""))
            lens_ax.yaxis.set_minor_formatter(CustomFormatStrFormatter(""))
            lens_ax.xaxis.set_minor_locator(MultipleLocator(0.1))
            lens_ax.yaxis.set_minor_locator(MultipleLocator(0.1))
            lens_ax.yaxis.set_ticks_position("right")

        fig.canvas.draw_idle()


def _on_mouse_move(
    event: Any,
    fig: Figure,
    ax: Axes,
    lens_ax: Axes,
    lens_im: Any,
    lens_state: Dict[str, Any],
    delta_log: float,
) -> None:
    """
    Handle mouse move events to update the lens view when the mouse moves.

    Parameters
    ----------
    event (matplotlip.event): the mouse move event
    fig (matplotlib.figure.Figure): the figure containing the axes
    ax (matplotlib.axes.Axes): the main axes
    lens_ax (matplotlib.axes.Axes): the lens axes
    lens_im (matplotlib.image.AxesImage): the image in the lens
    lens_state (dict): dictionary tracking the lens state
    delta_log (float): the delta in log10 space for the lens
    """
    if lens_state["active"] and event.inaxes == ax:
        mouse_x, mouse_y = event.xdata, event.ydata
        if mouse_x is None or mouse_y is None:
            return

        # Adjust lens shape in log-log space with an aspect ratio.
        aspect_ratio = ax.get_position().height / ax.get_position().width
        delta_log_x = delta_log * aspect_ratio
        delta_log_y = delta_log

        new_xlim = (mouse_x / 10 ** delta_log_x, mouse_x)
        new_ylim = (mouse_y, mouse_y * 10 ** delta_log_y)

        # Convert data limits to display coords.
        trans = ax.transData
        p1 = trans.transform((new_xlim[0], new_ylim[0]))
        p2 = trans.transform((new_xlim[1], new_ylim[1]))
        bbox_disp = mtransforms.Bbox.from_extents(
            min(p1[0], p2[0]),
            min(p1[1], p2[1]),
            max(p1[0], p2[0]),
            max(p1[1], p2[1]),
        )

        # Ensure the canvas is updated so we can capture fresh pixels.
        fig.canvas.draw()

        # Copy pixel region from the main Axes area of the figure.
        region = asarray(fig.canvas.copy_from_bbox(bbox_disp))
        # Remove alpha channel if present.
        region_rgb = region[..., :3]

        # Update the lens image data and set the new extent.
        lens_im.set_data(region_rgb)
        lens_im.set_extent(
            [new_xlim[0], new_xlim[1], new_ylim[0], new_ylim[1]])

        # Update the lens Axes limits to match.
        lens_ax.set_xlim(new_xlim)
        lens_ax.set_ylim(new_ylim)

        fig.canvas.draw_idle()
