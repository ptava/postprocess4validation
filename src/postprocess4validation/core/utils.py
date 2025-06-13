from logging import getLogger, WARNING
from typing import Union, cast
from enum import Enum
from argparse import ArgumentTypeError
from pathlib import Path
from os import getcwd
from getpass import getuser

# Logger for the module
logger = getLogger(__name__)
# Quiet the entire matplotlib stack
getLogger('matplotlib').setLevel(WARNING)
# Quiet the entire Pillow stack
getLogger("PIL").setLevel(WARNING)

class Info:
    pkg = cast(str, __package__)
    PACKAGE_NAME = pkg.split(".")[0]
    LAB = "SMART Lab - Biorobotic Institute"
    SCHOOL = "Scuola Superiore Sant'Anna di Pisa"
    USER = getuser()
    OUTPUT_DIR = getcwd()
    SUPPORTED_PLANE_TAGS = ["XY", "XZ", "YX", "YZ", "ZX", "ZY"]
    SUPPORTED_CHARACTERS = set("XYZ")

class DefaultValues:
    DEFAULT_TIME_FOR_DATASET = 0.0
    FLOW_DIR = 'X'

class LoaderKind(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"

def dir_path(dirpath: Union[str, Path]) -> Path:
    """
    Validate if the provided string is a valid directory path.
    """
    try:
        return validate_path(dirpath, must_exist=True, must_be_dir=True)
    except ValueError as e:
        raise ArgumentTypeError(str(e))

def file_path(filepath: Union[str, Path]) -> Path:
    """
    Validate if the provided string is a valid file path.
    """
    try:
        return validate_path(filepath, must_exist=True, must_be_file=True)
    except ValueError as e:
        raise ArgumentTypeError(str(e))

def output_path(string: str) -> Path:
    """
    Validate if the provided string is a valid output path.

    For output paths, we only check that the parent directory exists,
    not the file itself (which may not exist yet).

    """
    if not string:
        raise ArgumentTypeError("Output path cannot be empty")

    path_obj = Path(string)

    # Check if parent directory exists
    if not path_obj.parent.exists():
        raise ArgumentTypeError(f"Parent directory does not exist: {path_obj.parent}")

    return path_obj

def validate_path(
    path: Union[str, Path],
    must_exist: bool = True, 
    must_be_file: bool = False, 
    must_be_dir: bool = False
) -> Path:
    """
    Validate a file or directory path.

    Parameters
    ----------
    path (str): path to validate
    must_exist (bool, optional): whether the path must exist, default True
    must_be_file (bool, optional): whether the path must be a file, default False
    must_be_dir (bool, optional): whether the path must be a directory, default False

    Returns
    -------
    str: the validated path

    Raises
    ------
    ValueError: if the path is empty or doesn't meet the specified criteria
    """
    if not path:
        raise ValueError("Path cannot be empty")

    path_obj = Path(path)

    if must_exist and not path_obj.exists():
        raise ValueError(f"Path does not exist: {path_obj}")

    if must_be_file and not path_obj.is_file():
        raise ValueError(f"Path is not a file: {path_obj}")

    if must_be_dir and not path_obj.is_dir():
        raise ValueError(f"Path is not a directory: {path_obj}")

    return path_obj

def append_index_to_filename(file_path: Path, idx: int) -> Path:
    """ Append the index to the filename. """

    base, ext = file_path.stem, file_path.suffix
    new_name = f"{base}_{idx}{ext}"
    new_path = file_path.parent / new_name

    return new_path


