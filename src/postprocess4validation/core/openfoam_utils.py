from subprocess import run, PIPE
from pathlib import Path
from typing import Iterable, List
from os import scandir
from re import compile

from .utils import logger
from .exceptions import NoTimeFolderError

def find_postProcessing(start_path=".") -> List[Path]:
    """
    Emulates the bash command `find . -name postProcessing`.
    Searches for directories named 'postProcessing' starting from the given path.

    :param start_path: Directory path to start searching from.
    :return: List of paths where 'postProcessing' directories are found.
    """
    dirs = [p for p in Path(start_path).rglob("postProcessing") if p.is_dir()]
    return sorted(dirs)

def filter_postProcessing(
    dirs: List[Path],
    excluded: Iterable[str | Path],
    included: Iterable[str | Path] | None = None,
) -> List[Path]:
    """
    Include and exclude matching postProcessing directories from a discovered list.

    A value matches when it refers to the case folder name or an explicit path
    to the case folder or the postProcessing folder.
    """
    included_tokens: set[str] = set()
    if included is not None:
        for item in included:
            path = Path(item)
            included_tokens.update(_path_tokens(path))

    excluded_tokens: set[str] = set()
    for item in excluded:
        path = Path(item)
        excluded_tokens.update(_path_tokens(path))

    filtered_dirs = dirs
    if included_tokens:
        filtered_dirs = [
            directory
            for directory in filtered_dirs
            if not _path_tokens(directory).isdisjoint(included_tokens)
        ]

    return [
        directory
        for directory in filtered_dirs
        if _path_tokens(directory).isdisjoint(excluded_tokens)
    ]

def _path_tokens(path: Path) -> set[str]:
    tokens = {path.name, path.parent.name, str(path.resolve())}
    return {token for token in tokens if token and token != "."}

def get_latest_time_subfolder(path: Path) -> str:
    """
    Gets the latest time folder by sorting and extracting latest time value from
    the result of 'get_time_subfolders'.
    """
    folders = get_time_subfolders(path)
    latest = sorted(folders, key=float, reverse=True)[0]
    logger.debug(f"Found latest time folder: {latest} in {path}")
    return latest

def get_time_subfolders(path: Path) -> List[str]:
    """
    Gets the latest time folder from the given OpenFOAM postProcessing directory.

    Parameters
    ----------
    path (Path): Path to the OpenFOAM postProcessing directory.

    Returns
    -------
    List: List of string containing time folders names.
    """
    _TIME_FOLDER_PATTERN = compile(
        r"^\d+(?:\.\d+)?$"
    )
    time_folders = [
        d.name for d in scandir(path) 
        if d.is_dir() and _TIME_FOLDER_PATTERN.match(d.name)
    ]
    if not time_folders:
        raise NoTimeFolderError(
            f"No valid time folders found in {path}."
        )
    return time_folders

def is_openfoam_installed() -> bool:
    try:
        # Try to run a basic OpenFOAM command
        result = run(['which', 'blockMesh'], stdout=PIPE, stderr=PIPE, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error while checking OpenFOAM installation: {e}")
        return False
