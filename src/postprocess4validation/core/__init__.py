"""
Core package initialization.

This module initializes the core sub-package and exports its public interfaces.
"""

from .configure_logger import configure_logger
from .point_data import PointData
from .data_set import DataSet
from .line import Line
from .plane import Plane
from .plane_set import PlaneSet
from .exceptions import OpenFOAMError, NoTimeFolderError
from .openfoam_utils import (
    find_postProcessing,
    get_time_subfolders,
    get_latest_time_subfolder,
)
from .metrics_file_handler import (
        initialise_metrics_file,
        write_metrics,
)
from .csv_data_loader import CSVDataLoader
from .utils import (
    dir_path,
    file_path,
    output_path,
    validate_path,
    append_index_to_filename,
    LoaderKind,
    Info,
    DefaultValues,
)
from .data_loader import (
    LoaderRegistry,
    register_loader,
    DirectoryDataLoader,
    FileDataLoader,
)
from .visualization import (
    CustomFormatStrFormatter,
    get_marker,
    get_distinct_color,
    connect_save_event,
)


__all__ = [
    'configure_logger',
    'OpenFOAMError',
    'NoTimeFolderError',
    'PointData',
    'DataSet',
    'Line',
    'Plane',
    'PlaneSet',
    'find_postProcessing',
    'get_time_subfolders',
    'get_latest_time_subfolder',
    'initialise_metrics_file',
    'append_index_to_filename',
    'write_metrics',
    'dir_path',
    'file_path',
    'output_path',
    'LoaderKind',
    'validate_path',
    'CSVDataLoader',
    'LoaderRegistry',
    'register_loader',
    'DirectoryDataLoader',
    'Info',
    'FileDataLoader',
    'DefaultValues',
    'CustomFormatStrFormatter',
    'connect_save_event',
    'get_distinct_color',
    'get_marker',
]

