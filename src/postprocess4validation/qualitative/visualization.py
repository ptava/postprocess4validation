from typing import cast, List, Optional
from math import ceil
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import Slider
from matplotlib.axes import Axes
from numpy import atleast_1d
from numpy.typing import NDArray
from os import environ
from pathlib import Path
from trimesh import load_mesh
from trimesh.path.traversal import discretize_path
import numpy as np

from ..core import (
    PlaneSet,
    Plane,
    connect_save_event,
    append_index_to_filename,

)
from .utils import DefaultValues, PlotConstants, logger


def create_plots(
    planes: PlaneSet,
    file_path: Path,
    save_only: bool,
    last_timestep_only: bool,
    interactive: bool,
    geometry: Optional[Path] = None,
    plot_hsize: float = PlotConstants.PLOT_SIZE[0],
    plot_vsize: float = PlotConstants.PLOT_SIZE[1],
    max_columns: int = PlotConstants.FIGURE_MAXCOLUMNS,
    max_height: float = PlotConstants.FIGURE_MAXHEIGHT,
    min_lines_per_plane: int = DefaultValues.MIN_LINES_PER_PLANE

) -> None:
    """
    Create plots for the given planes.

    The function does:
    1. Filter planes without data
    2. Group planes with data by their 'tag'
    3. Plot all selected planes (one figure for each group -> split in multiple chunks
        if required)

    Parameters:
    ----------
        planes (PlaneSet): The set of planes to plot.
        file_path (Path): The path to save the plot.
        save_only (bool): If True, save the plot without showing it.
        last_timestep_only (bool): If True, plot only the last timestep data for
            each simulation data.
        interactive (bool): If True, enable interactive features like widgets.
        plot_hsize (optional, float): Width of the figure in inches.
        plot_vsize (optional, float): Height of the figure in inches.
        max_columns (optional, int): Number of columns in the plot layout.
        max_height (optional, float): Maximum height of the figure in inches.

    """
    plottable_planes = planes.filter_planes_by_data(min_lines_per_plane)
    planes_by_tag = plottable_planes.group_planes_by_tag()

    for tag, plane_set in planes_by_tag.items():
        if not plane_set:
            raise ValueError(f"No planes found for tag '{tag}'.")

        logger.info(
            f"Plotting tag '{tag}' with {len(plane_set)} planes"
        )

        _plot_tagged_plane_set(
            plane_set=plane_set,
            base_path=file_path,
            save_only=save_only,
            last_timestep_only=last_timestep_only,
            interactive=interactive,
            geometry=geometry,
            plot_hsize=plot_hsize,
            plot_vsize=plot_vsize,
            max_columns=max_columns,
            max_height=max_height,
        )


def _create_interactive_slider(
    fig: Figure,
    axes: NDArray,
    current_set: PlaneSet,
    fields: List[str],
    n_fields: int,
    last_timestep_only: bool,
) -> None:
    ax_slider = fig.add_axes(PlotConstants.SLIDER_POSITION)
    slider = Slider(
        ax=ax_slider,
        label='Scale:',
        valmin=0,
        valmax=0.5,
        valinit=DefaultValues.FIELD_SCALE,
        valstep=0.001,
        initcolor='none',
    )

    def update(val: float) -> None:
        for ax in axes:
            ax.clear()
        scale = slider.val
        for i_plane, plane in enumerate(current_set):
            for j, field_name in enumerate(fields):
                idx = i_plane * n_fields + j
                if idx >= len(axes):
                    logger.warning(
                        f"Index {idx} exceeds axes length {len(axes)}."
                    )
                    continue    # Skip if index exceeds axes length
                plane.add_to_plot(
                    ax=axes[idx],
                    field_name=field_name,
                    last_timestep_only=last_timestep_only,
                    scale=scale,
                )

    slider.on_changed(update)


def _add_geometry(
        _ax: Axes,
        _path: Path,
        _plane: Plane,
        _facecolor='tab:grey',
        _edgecolor='k',
        _alpha=0.75) -> None:
    """ Add geometry from an STL file to the 2D axes if a planar intersection is found. """
    try:
        stl_mesh = load_mesh(_path.as_posix())

        section = stl_mesh.section(
            plane_origin=_plane.origin,
            plane_normal=_plane.normal
        )

        if section is None:
            logger.warning(
                f"No intersection found for {_path} with given plane.")
            return

        loops_3d = section.discrete

        # Figure out which axis is constant
        normal = np.asarray(_plane.normal, dtype=float)
        normal /= np.linalg.norm(normal)
        principal = int(np.argmax(np.abs(normal)))
        # principal == 0 → drop X (keep Y,Z)
        # principal == 1 → drop Y (keep X,Z)
        # principal == 2 → drop Z (keep X,Y)
        keep_axes = [i for i in (0, 1, 2) if i != principal]

        for loop in loops_3d:
            pts2d = loop[:, keep_axes]

            _ax.fill(
                pts2d[:, 0],
                pts2d[:, 1],
                facecolor=_facecolor,
                edgecolor=_edgecolor,
                linewidth=1.0,
                alpha=_alpha
            )

    except Exception as e:
        logger.warning(f"Could not load or process STL {_path}: {e}")


def _plot_plane_set(
    plane_set: PlaneSet,
    axes: NDArray,
    fields: List[str],
    n_fields: int,
    last_timestep_only: bool,
    geometry: Optional[Path],
) -> None:
    for i_plane, plane in enumerate(plane_set):

        plane.assign_points_to_lines()

        for j, field_name in enumerate(fields):
            idx = i_plane * n_fields + j

            if idx >= len(axes):
                logger.warning(
                    f"Index {idx} exceeds axes length {len(axes)}."
                )
                continue    # Skip if index exceeds axes length
            plane.add_to_plot(
                ax=axes[idx],
                field_name=field_name,
                last_timestep_only=last_timestep_only,
                scale=DefaultValues.FIELD_SCALE,
            )

            if geometry:
                _add_geometry(axes[idx], geometry, plane)


def _plot_tagged_plane_set(
    plane_set: PlaneSet,
    base_path: Path,
    save_only: bool,
    last_timestep_only: bool,
    interactive: bool,
    geometry: Optional[Path],
    plot_hsize: float,
    plot_vsize: float,
    max_columns: int,
    max_height: float,
) -> None:
    n_fields = len(plane_set.fields)
    total_subplots = len(plane_set) * n_fields

    columns = min(max_columns, total_subplots)
    max_rows = max(1, int(max_height / plot_vsize))
    subplots_per_fig = max_rows * columns

    for start in range(0, total_subplots, subplots_per_fig):
        chunk_size = min(subplots_per_fig, total_subplots - start)
        rows = ceil(chunk_size / columns)

        fig, axes = plt.subplots(
            rows,
            columns,
            figsize=(plot_hsize * columns, plot_vsize * rows),
        )

        fig = cast(Figure, fig)
        axes = atleast_1d(axes).flatten()

        # Slice PlaneSet to get the current set of planes to plot
        planes_in_chunk = ceil(chunk_size / n_fields)
        first_plane_idx = start // n_fields
        current_set = plane_set.slice(
            first_plane_idx,
            first_plane_idx + planes_in_chunk
        )
        _plot_plane_set(
            current_set,
            axes,
            fields=list(plane_set.fields),
            n_fields=n_fields,
            last_timestep_only=last_timestep_only,
            geometry=geometry,
        )

        if interactive:
            fig.tight_layout(rect=[0, 0.10, 1, 1])
            _create_interactive_slider(
                fig=fig,
                axes=axes,
                current_set=current_set,
                fields=list(plane_set.fields),
                n_fields=n_fields,
                last_timestep_only=last_timestep_only,
            )
        else:
            fig.tight_layout()

        current_path = append_index_to_filename(
            base_path, start // subplots_per_fig)

        if save_only or environ.get("DISPLAY") is None:
            fig.savefig(current_path)
        else:
            connect_save_event(fig, current_path)
            try:
                plt.show()
            except UserWarning as e:
                logger.warning(
                    f"Error showing plot: {e}\n"
                    f"Saving to {current_path} instead."
                )
                fig.savefig(current_path)
