from __future__ import annotations
from os import environ
from re import compile, IGNORECASE
from mplcursors import cursor
from random import random
from math import ceil
from typing import Dict, Any, List, Optional, cast
from pathlib import Path
from stl import mesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection as Scatter
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.ticker import (
    LogLocator,
    MultipleLocator,
    NullFormatter
)
from numpy import (
    exp as np_exp,
    max as np_max,
    min as np_min,
    log,
    linspace,
    array,
    ndarray
)

from ..core import (
    DataSet,
    CustomFormatStrFormatter,
    get_distinct_color,
    get_marker,
    connect_save_event,
    append_index_to_filename,
)
from .utils import (
    logger,
    PlotConstants,
    MetricNames,
    safe_array_conversion
)
from .zoom import add_interactive_lens


def define_2Dplot_storage() -> Dict[str, Any]:
    """
    Define a custom dictionary to store data for the 2D scatter plot.
    """

    return {
        "field_marker_map": {},
        "all_scatter_args": [],
        "all_mg_vals": [],
        "all_vg_vals": [],
        "fields": set(),
        "colors": [],
        "labels": [],
    }


def store_2Dplot_data(
    data_storage: Dict[str, Any],
    source: str,
    statistics: Dict,
    last_time_only: bool = False
) -> None:
    """
    Store data for a 2D scatter plot from the provided statistics.

    Parameters
    ----------
    data_storage (Dict[str, Any]): dictionary to store plot data
    source (str): source identifier for the data (e.g., simulation name)
    statistics (dict): metrics stored as dictionary with structure:
        {
            "NMSE": {time1: {field1: val, field2: val, ...}, time2: {...}, ...},
            "MG":   {time1: {...}, time2: {...}, ...},
            "GV":   {time1: {...}, time2: {...}, ...},
        }
    last_time_only (bool, optional): if True, only plot metrics for the last
    time step, by default False

    Raises
    ------
    ValueError: if required metrics are missing or invalid
    """
    logger.info(f"Storing data for plot from source: {source}")

    if MetricNames.MG not in statistics or MetricNames.GV not in statistics:
        logger.error(
            f"Required metrics missing: {MetricNames.MG} or {MetricNames.GV} "
            "not found in statistics")
        raise ValueError(
            f"Cannot fill plot: '{MetricNames.MG}' or '{MetricNames.GV}' not "
            "found in statistics.")

    mg_data = statistics[MetricNames.MG]
    vg_data = statistics[MetricNames.GV]

    if not mg_data or not vg_data:
        logger.error("Empty metric data provided")
        raise ValueError("Empty metric data provided.")

    times = sorted(mg_data.keys())
    if not times:
        logger.error("No time steps found in the data")
        raise ValueError("No time steps found in the data.")

    if last_time_only and times:
        logger.info("Using only the last time step")
        times = [times[-1]]

    # Figure out which fields exist
    all_fields = data_storage["fields"]
    for t in mg_data:
        all_fields.update(mg_data[t].keys())

    logger.debug(f"Found {len(all_fields)} unique fields in the data")

    # Assign each field a unique marker - do this once
    field_marker_map = {}
    for i, fields in enumerate(sorted(all_fields)):
        field_marker_map[fields] = get_marker(i)
        data_storage["field_marker_map"][fields] = field_marker_map[fields]

    # Process each time step
    h_start = random()  # Random starting hue for this dataset

    for time_idx, time_key in enumerate(times):
        # Get color for this time step
        current_color = get_distinct_color(time_idx, h_start)
        data_storage["colors"].append(current_color)

        # Get data for this time step
        mg_per_field = mg_data[time_key]
        vg_per_field = vg_data.get(time_key, {})

        logger.debug(
            f"Processing time step {time_key} with {len(mg_per_field)} fields")

        # Remember time-label for legend building
        if last_time_only:
            data_storage["labels"].append(source)
        else:
            data_storage["labels"].append(time_key)

        # Process each field
        for field_key, mg_val in mg_per_field.items():
            if field_key not in vg_per_field:
                logger.warning(
                    f"Field {field_key} missing from {MetricNames.GV} data at "
                    f"time {time_key}"
                )
                continue

            vg_val = vg_per_field[field_key]

            if mg_val <= 0 or vg_val <= 0:
                logger.warning(
                    f"Invalid values for field {field_key} at time {time_key}: "
                    f"MG={mg_val}, GV={vg_val}")
                continue

            # Plot scatter
            marker_style = field_marker_map[field_key]

            # Store data for final axis limit computations
            data_storage["all_mg_vals"].append(mg_val)
            data_storage["all_vg_vals"].append(vg_val)

            # Build label for hover
            label_text = (
                f"Time: {source}-{time_key}\n"
                f"Field: {field_key}\n"
                f"MG={mg_val:.3f}, GV={vg_val:.3f}"
            )

            scatter_args = {
                "x": mg_val,
                "y": vg_val,
                "color": current_color,
                "marker": marker_style,
                "text": label_text
            }

            data_storage["all_scatter_args"].append(scatter_args)

    logger.info(
        f"Added {len(data_storage['all_mg_vals'])} data points to the plot")


def create_2Dplot(
    data_storage: Dict[str, Any],
    file_path: Path,
    save_only: bool,
    interactive: bool,
    plot_margin: float = PlotConstants.MARGIN,
    linewidth: float = PlotConstants.LINEWIDTH
) -> None:
    """
    Create a 2D scatter plot in a figure, formatting it, add scatter points,
    show if required and save plot.

    Parameters
    ----------
    data_storage (Dict[str, Any]): dictionary containing plot data
    file_path (Path): path to save the plot
    save_only (bool): if True, save the plot without showing it
    interactive (bool): if True, add an interactive lens to the plot
    plot_margin (float, optional): margin factor for axis limits, by default
        PlotConstants.MARGIN
    linewidth (float, optional): line width for reference lines, by default
        PlotConstants.LINEWIDTH

    """
    def _format_plot(
            all_mg_vals: ndarray,
            all_vg_vals: ndarray,
            ax: Axes
    ) -> None:
        # Set log scales
        ax.set_xscale('log')  # type: ignore[arg-type]
        ax.set_yscale('log')  # type: ignore[arg-type]

        # Labels
        ax.set_xlabel(MetricNames.MG)
        ax.set_ylabel(MetricNames.GV)

        # Set x and y ticks locators and formats
        major_locator = LogLocator(base=2.0)
        minor_locator_x = MultipleLocator(0.25)
        minor_locator_y = MultipleLocator(0.25)
        ax.xaxis.set_major_locator(major_locator)
        ax.yaxis.set_major_locator(major_locator)
        ax.xaxis.set_minor_locator(minor_locator_x)
        ax.yaxis.set_minor_locator(minor_locator_y)
        ax.xaxis.set_major_formatter(CustomFormatStrFormatter(''))
        ax.yaxis.set_major_formatter(CustomFormatStrFormatter(''))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.xaxis.set_ticks_position('bottom')
        ax.tick_params(which='major', width=1.00, length=5)
        ax.tick_params(which='minor', width=0.75, length=2.5)
        ax.grid(
            True, which='both', linestyle='--',
            linewidth=0.5, color='tab:grey', alpha=0.35
        )

        # Change default spines visualization
        ax.spines[['right', 'top']].set_visible(False)

        # Title
        title = 'Comparative analysis'
        ax.set_title(title, fontsize=14,
                     fontname='Monospace', color='tab:blue')

        # Adjust plot limits
        # Compute global max
        max_mg = np_max(all_mg_vals)
        max_vg = np_max(all_vg_vals)

        # Expand ranges for a comfortable margin
        mg_max_for_plot = max(2.0, max_mg) * plot_margin
        mg_min_for_plot = 1 / mg_max_for_plot
        vg_min_for_plot = 1.0
        vg_max_for_plot = max(2.0, max_vg) * plot_margin
        ax.set_xlim(mg_min_for_plot, mg_max_for_plot)
        ax.set_ylim(vg_min_for_plot, vg_max_for_plot)

        logger.debug(
            f"Set plot limits: x=[{mg_min_for_plot}, {mg_max_for_plot}], "
            f"y=[{vg_min_for_plot}, {vg_max_for_plot}]")

        # Draw reference curve
        mg_curve = linspace(0.01, mg_max_for_plot, 300)
        vg_curve = np_exp(log(mg_curve)**2)
        ax.plot(mg_curve, vg_curve, color='k',
                linewidth=linewidth)

        # Factor of 2 lines
        ax.axvline(x=0.5, color='tab:gray', linestyle='--',  # type: ignore[arg-type]
                   linewidth=linewidth)
        ax.axvline(x=2.0, color='tab:gray', linestyle='--',  # type: ignore[arg-type]
                   linewidth=linewidth)

        logger.debug("Added reference curve and factor-of-two lines")

    def _build_legend(colors, fields, labels, ax: Axes) -> None:
        legend_entries = []
        legend_labels = []

        # Factor-of-two lines (dummy handle)
        f2_handle = Line2D([], [], color='black', linestyle='--')
        legend_entries.append(f2_handle)
        legend_labels.append("Factor-of-2 lines")

        # Reference curve (dummy handle)
        ref_handle = Line2D([], [], color='tab:gray', linestyle='-')
        legend_entries.append(ref_handle)
        legend_labels.append("ln(VG)=ln(MG)^2")

        # Field markers: each field gets a black marker
        for f_name in fields:
            field_handle = Line2D(
                [],
                [],
                color='black',
                marker=marker_map[f_name],
                linestyle='None',
                markersize=7
            )
            legend_entries.append(field_handle)
            legend_labels.append(f_name)

        # Labels: show colors with common 'o' shape
        time_marker = 'o'
        for color, label in zip(colors, labels):
            color_handle = Line2D([], [], color=color, marker=time_marker,
                                  linestyle='None', markersize=7)
            legend_entries.append(color_handle)
            legend_labels.append(label)

        # Create legend
        ax.legend(legend_entries, legend_labels, bbox_to_anchor=(1.05, 1),
                  loc='upper left', borderaxespad=0.)

        logger.debug(f"Created legend with {len(legend_entries)} entries")

    # return a scatter object to the axes
    def _add_scatter_obj(ax: Axes, scatter_args: Dict) -> Scatter:
        """
        Plot scatter points on the axes with arguments from the scatter_label_map.
        """
        # Create scatter object
        scatter = ax.scatter(
            scatter_args["x"],
            scatter_args["y"],
            color=scatter_args["color"],
            marker=scatter_args["marker"],
        )
        return scatter

    # Check if data storage has been filled
    if not data_storage or not data_storage["all_mg_vals"]:
        logger.error("No data found to finalize")
        raise ValueError(
            "No data found to finalize. Fill the plot with data first.")

    # Retrieve data from storage
    all_mg_vals = array(data_storage["all_mg_vals"])
    all_vg_vals = array(data_storage["all_vg_vals"])
    marker_map = data_storage["field_marker_map"]
    fields_data = data_storage["fields"]
    labels_data = data_storage["labels"]
    colors_data = data_storage["colors"]
    all_scatter_args = data_storage["all_scatter_args"]

    # Create plot with all scatter objects created from the data storage
    logger.info("Creating 2D scatter plot")

    fig, ax = plt.subplots(figsize=PlotConstants.PLOT2D_FIGSIZE)

    # Tell type checker their are figure and axes
    fig = cast(Figure, fig)
    ax = cast(Axes, ax)

    scatter_label_map: Dict[Scatter, str] = {}
    for scatter_args in all_scatter_args:
        scatter = _add_scatter_obj(ax, scatter_args)
        scatter_label_map[scatter] = scatter_args["text"]

    # Attach mplcursor
    cur = cursor(scatter_label_map.keys(), hover=True)

    @cur.connect("add")
    def on_add(sel):
        sc_obj = sel.artist
        sel.annotation.set_text(scatter_label_map.get(sc_obj, ""))
        sel.annotation.get_bbox_patch().set_facecolor("tab:blue")
        sel.annotation.get_bbox_patch().set_alpha(0.4)

    # Change the default plot appearance and create the plot legend
    _format_plot(all_mg_vals, all_vg_vals, ax)
    _build_legend(colors_data, fields_data, labels_data, ax)

    # Add interactive lens if requested
    if interactive:
        logger.info("Adding interactive lens to the plot")
        add_interactive_lens(fig, ax)

    # Define the layout and show the plot
    fig.tight_layout()

    # Save or show the figure
    if save_only or environ.get("DISPLAY") is None:
        fig.savefig(file_path)
    else:
        connect_save_event(fig, file_path)
        try:
            plt.show()
        except UserWarning as e:
            logger.warning(
                f"Error showing plot: {e}\n"
                f"Saving to {file_path} instead."
            )
            fig.savefig(file_path)


def find_matching_fields(
    dataset: DataSet,
    name: str = PlotConstants.PLOT3D_FIELD
) -> List[str]:
    """
    Find all mathcing fields in the dataset with regex from input string.

    Parameters
    ----------
    dataset (DataSet): The dataset to search for fields names
    name (str): The name to search for in the dataset fields.

    Returns
    -------
    list[str]: List of field names that match the provided name.
    """
    # Basic pattern matches everything contains 'name' 
    # (both lower and upper case)
    _BASIC_PATTERN = compile(rf".*{name}.*", IGNORECASE)

    # Get all fields in the dataset (bad practice)
    all_fields = dataset.fields.keys()

    matching = [field for field in all_fields if _BASIC_PATTERN.match(field)]
    logger.debug(f"Found {len(matching)} fields matching '{name}'")

    if not matching:
        msg = f"No fields found matching '{name}' in the dataset"
        logger.error(msg)
        raise ValueError(msg)
    return matching


def define_3Dplot_storage(
    dataset: DataSet,
) -> Dict[str, Any]:
    """
    Define a custom dictionary to store data for the 3D scatter plot.

    Parameters
    ----------
    dataset (DataSet): The dataset containing the points and fields info.

    Returns
    -------
    Dict[str, Any]: A dictionary to store data for the 3D scatter plot.
    """

    return {
        'fields': [],               # names of plotted fields
        'fields_values': [],       # field values for each field
        'labels': [],               # labels for each field
        'sources': [],               # source of the data (e.g., simulation name)
        # TODO: why? replace the usage of all coordinates by using pointData 
        # methods
        'coordinates': safe_array_conversion(dataset.get_all_coordinates()),
    }


def store_3Dplot_data(
    dataset: DataSet,
    data_storage: Dict[str, Any],
    last_time_only: bool = False,
) -> None:
    """
    Store data for a 3D scatter plot from the provided dataset.

    Parameters
    ----------
    dataset (DataSet): The dataset containing the points and field values.
    data_storage (Dict[str, Any]): The storage dictionary to fill with data.
    last_time_only (bool, optional): If True, only plot the last time step,

    """
    fields = find_matching_fields(dataset)
    data_storage['fields'] = fields     # persist for future operations

    # Get times
    times = sorted(dataset.get_all_times())
    if last_time_only and times:
        logger.info("Using only the last time step")
        times = [times[-1]]

    for field in fields:
        for time in times:
            field_values = dataset.get_field_values(field, time)
            if field_values is None:
                logger.warning(
                    f"Field {fields} not found in dataset at time {time}")
                continue

            # Store scatter objects and tags for future operations
            label = f"{field} @ {time}"
            data_storage['labels'].append(
                label
            )
            data_storage['sources'].append(
                dataset.source
            )
            data_storage['fields_values'].append(
                safe_array_conversion(field_values)
            )


def create_3Dplot(
    data_storage: Dict[str, Any],
    file_path: Path,
    save_only: bool = False,
    geometry: Optional[Path] = None,
    ncols: int = PlotConstants.MAX_COLS,
) -> None:
    """
    Finalize a 3D scatter plot by organizing it into one or more figures
    based on available vertical space.

    Parameters
    ----------
    data_storage (Dict[str, Any]): dictionary containing plot data
    file_path (Path): path to save the plot
    save_only (bool): if True, save the plot without showing it
    geometry (Optional[Path]): path to an STL file for geometry overlay, by
        default None
    ncols (int): number of columns in the plot grid, by default
        PlotConstants.MAX_COLS
    """

    def _add_geometry(ax3d: Axes, path: Path) -> None:
        """ Add geometry from an STL file to the 3D axes. """
        try:
            stl_mesh = mesh.Mesh.from_file(path.as_posix())
            collection = Poly3DCollection(
                stl_mesh.vectors,
                alpha=0.5,
                linewidths=0.1,
                edgecolors='k',
                facecolors='tab:grey'
            )
            ax3d.add_collection3d(collection)
        except Exception as e:
            logger.warning(f"Could not load STL: {e}")

    def _format_3d_axes(ax3d: Axes, scatter, label: str, values: ndarray,
                        coords: ndarray, title: str) -> None:
        """ Format the 3D axes with labels, limits, and colorbar. """

        ax3d.set_title(title, fontsize=14,
                       fontname='Monospace', color='tab:blue')

        ax3d.set_xlabel("X")
        ax3d.set_ylabel("Y")

        max_range = np_max([
            np_max(coords[:, 0]) - np_min(coords[:, 0]),
            np_max(coords[:, 1]) - np_min(coords[:, 1]),
            np_max(coords[:, 2]) - np_min(coords[:, 2])
        ])
        mid_x = (np_max(coords[:, 0]) + np_min(coords[:, 0])) / 2
        mid_y = (np_max(coords[:, 1]) + np_min(coords[:, 1])) / 2
        mid_z = (np_max(coords[:, 2]) + np_min(coords[:, 2])) / 2

        ax3d.set_xlim(mid_x - max_range / 2, mid_x + max_range / 2)
        ax3d.set_ylim(mid_y - max_range / 2, mid_y + max_range / 2)
        ax3d.set_zlim(mid_z - max_range / 2, mid_z + max_range / 2)

        ax3d.view_init(
            elev=PlotConstants.PLOT3D_EL,
            azim=PlotConstants.PLOT3D_AZ
        )

        ax3d.figure.colorbar(
            scatter,
            ax=ax3d,
            label=label,
            shrink=0.50,
            aspect=20,
            pad=0.10
        )

        cur = cursor(scatter, hover=True)

        @cur.connect("add")
        def _on_add(sel) -> None:
            sel.annotation.set_text(
                f"{label}\n"
                f"Point: {sel.index} at {coords[sel.index]}\n"
                f"Value: {values[sel.index]:.3f}"
            )
            sel.annotation.get_bbox_patch().set_facecolor("tab:blue")
            sel.annotation.get_bbox_patch().set_alpha(0.4)


    def _plot_figure(
            slabs_group,
            labels_group,
            sources_group,
            idx,
            coords,
            field_minmax,
    ) -> None:
        rows = ceil(len(slabs_group) / ncols)
        fig = plt.figure(
            figsize=(
                PlotConstants.PLOT3D_FIGSIZE[0] * ncols,
                subplot_height * rows
            )
        )

        grid = GridSpec(rows, ncols, figure=fig)

        for i, (values, label, source) in enumerate(
                zip(slabs_group, labels_group, sources_group)):
            # Get position in the grid and create 3D subplot
            row, col = divmod(i, ncols)
            ax3d = fig.add_subplot(grid[row, col], projection="3d")

            # Retrieve the min and max values for the color scale
            field_name = label.split("@")[0].strip() # BAD: Linked to how is stored
            vmin, vmax = field_minmax.get(field_name, (None, None))

            # Add scatter object to the 3D axes
            scatter = ax3d.scatter(
                coords[:, 0], coords[:, 1], coords[:, 2],
                c=values,
                cmap=PlotConstants.PLOT3D_CMAP,
                marker="o",
                vmin=vmin,
                vmax=vmax,
            )

            _format_3d_axes(ax3d, scatter, label, values, coords, source)

            if geometry:
                _add_geometry(ax3d, geometry)

            logger.debug(f"Added 3D scatter plot for {label}")

        # set figure layout
        fig.tight_layout()

        # Change the basename of the file path for the current figure
        current_file_path = append_index_to_filename(file_path, idx)

        # Save or show the figure
        if save_only or environ.get("DISPLAY") is None:
            fig.savefig(current_file_path)
        else:
            connect_save_event(fig, current_file_path)
            try:
                plt.show()
            except UserWarning as e:
                logger.warning(
                    f"Error showing plot: {e}\n"
                    f"Saving to {current_file_path} instead."
                )
                fig.savefig(current_file_path)

    # Retrieve data from storage
    coords: ndarray = data_storage["coordinates"]
    labels: List[str] = data_storage["labels"]
    slabs: List[ndarray] = data_storage["fields_values"]
    sources: List[str] = data_storage["sources"]

    # Compute global vmin/vmax per field
    field_minmax = {}
    for lbl, vals in zip(labels, slabs):
        field = lbl.split("@")[0].strip() #BAD
        cur_min = float(np_min(vals))
        cur_max = float(np_max(vals))
        if field in field_minmax:
            prev_min, prev_max = field_minmax[field]
            field_minmax[field] = (
                min(prev_min, cur_min), max(prev_max, cur_max))
        else:
            field_minmax[field] = (cur_min, cur_max)

    # Check if there are any subplots to create
    n_subplots = len(slabs)
    if n_subplots == 0:
        logger.error("No subplots to create.")
        raise ValueError("No subplots to create.")

    # Layout calculation
    ncols = min(ncols, n_subplots)
    subplot_height = PlotConstants.PLOT3D_FIGSIZE[1]
    max_rows_per_fig = max(
        1, int(PlotConstants.PLOT3D_FIGMAXHEIGHT // subplot_height)
    )
    subplots_per_fig = max_rows_per_fig * ncols

    # Dispatch figures
    for i in range(0, n_subplots, subplots_per_fig):
        group_slabs = slabs[i:i + subplots_per_fig]
        group_labels = labels[i:i + subplots_per_fig]
        group_sources = sources[i:i + subplots_per_fig]
        _plot_figure(
            group_slabs,
            group_labels,
            group_sources,
            i // subplots_per_fig,
            coords,
            field_minmax,
        )
