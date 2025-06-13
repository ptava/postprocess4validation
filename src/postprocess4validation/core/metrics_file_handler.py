from typing import Union, Optional, Dict, Tuple
from datetime import datetime
from csv import writer
from getpass import getuser
from importlib import metadata
from pathlib import Path

from .exceptions import MetricsFileError
from .utils import logger, Info


def _get_package_info() -> Tuple[str, str]:
    """
    Retrieves the software name and version from an installed Python package.

    :param package_name: The name of the package to check.
    :return: (Software Name, Version) as a tuple.
    """
    try:
        version = metadata.version(Info.PACKAGE_NAME)
        return Info.PACKAGE_NAME, version
    except metadata.PackageNotFoundError:
        return Info.PACKAGE_NAME, "Unknown"


def initialise_metrics_file(
        path: Path,
        author: Optional[str] = None,
        lab: Optional[str] = None,
        school: Optional[str] = None
) -> None:
    """
    Initialize a metrics file with a metadata header. Overwrites the file if it 
    already exists.

    Parameters
    ----------
    path (Union[str, Path]): Path to the output metrics file.
    package_name (Optional, str): Name of the package generating the metrics.
    author (Optional, str): Name of the author. Defaults to the current system user.
    lab (Optional, str): Name of the reference laboratory. Defaults to a predefined 
        value.
    school (Optional, str): Name of the school/institution. Defaults to a predefined
        value.
        
    Raises
    ------
    MetricsFileError
        If there is an error writing to the file.

    """
    # Remove file if already exists
    if path.exists():
        path.unlink()

    software_name, software_version = _get_package_info()
    header_info = [
        ["Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Software", software_name],
        ["Version", software_version],
    ]
    # Add additional metadata if not None
    if school:
        header_info.append(["School", school])
    if lab:
        header_info.append(["Reference Laboratory", lab])
    if author:
        header_info.append(["Author", author])
    header_info.append([])  # Empty line for separation
    try:
        with open(path, "w+", newline="") as file:
            file_writer = writer(file)
            file_writer.writerows(header_info)
    except IOError as e:
        raise MetricsFileError(f"Error writing to file {path}: {e}")


def write_metrics(
    path: Path,
    identifier: str, 
    metrics_dict: Dict,
    last_time_only: bool = False,
    decimal_places: int = 3,
) -> None:
    """
    Appends computed statistical metrics to an existing table or creates a new 
    one if needed.

    :param path: Path to the CSV file where the table will be stored.
    :param metrics_dict: Dictionary of statistical metrics with time steps and fields.
    """
    if not metrics_dict:
        logger.warning("Metrics dictionary is empty. No data to write.")
        return

    try:
        # Extract time values in sorted order
        time_values = sorted(set(time for metric in metrics_dict for time in metrics_dict[metric]))

        if last_time_only:
            time_values = [time_values[-1]]  # Keep only the latest time value

        # Extract field names dynamically
        first_metric = next(iter(metrics_dict))
        first_time = next(iter(metrics_dict[first_metric]))
        field_names = metrics_dict[first_metric][first_time].keys()

        # Create table headers
        table_header = ["Id"] + [
            f"{metric}-{field}" for metric in metrics_dict for field in field_names
        ]

        # Prepare data rows
        data_rows = []
        for time in time_values:
            if last_time_only:
                row = [identifier]  # Use the passed identifier
            else:
                row = [time]
            for metric in metrics_dict:
                for field in metrics_dict[metric][time]:
                    value = metrics_dict[metric][time][field]
                    row.append(round(value, decimal_places))
            data_rows.append(row)
    except (KeyError, TypeError, ValueError, IndexError) as e:
        logger.error(f"Error processing metrics data: {e}")
        raise MetricsFileError(f"Error processing metrics dictionary: {e}")

    try:
        with open(path, "a", newline="") as file:
            file_writer = writer(file)
            logger.debug(f"Writing header to {path}")
            file_writer.writerow(table_header)
            logger.debug(f"Appending {len(data_rows)} rows to {path}")
            file_writer.writerows(data_rows)
        logger.info(f"Metrics written to {path} successfully.")
    except IOError as e:
        logger.error(f"Error writing to file {path}: {e}")
        raise MetricsFileError(f"Error writing to file {path}: {e}")
