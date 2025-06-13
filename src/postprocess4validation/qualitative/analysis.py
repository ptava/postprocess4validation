from typing import Type
from pathlib import Path

from ..core import (
    PlaneSet,
    DirectoryDataLoader,
    FileDataLoader,
)
from .utils import logger, FilePaths
from .lines_data_loader import OpenFOAMLinesLoader


def run_qualitative_analysis(
    simulation_paths: list[Path],
    directory_loader: Type[DirectoryDataLoader],
    file_loader: Type[FileDataLoader],
    plane_set: PlaneSet,
) -> None:
    """
    Run qualitative analysis on simulation data.

    This function:
    1. Process simulation data using the provided simulation loaders
    2. Add all the processed info into 'plane_set' argument

    Parameters:
    -----------
    simulations_paths (List[Path]): paths to the simulation data folders
    directory_loader (Type[DirectoryDataLoader]): class to load folder
    file_loader (Type[FileDataLoader]): class to load file
    plane_set (PlaneSet): set of available planes to store data in
    """
    for idx, sim_path in enumerate(simulation_paths):
        logger.info(
            f"Processing simulation: {sim_path.resolve()}"
            f"[{idx}/{len(simulation_paths)-1}]"
        )
        load_data_into_planeset(
            plane_set=plane_set,
            directory_loader=directory_loader,
            file_loader=file_loader,
            data_path=sim_path,
        )


def load_data_into_planeset(
    plane_set: PlaneSet,
    directory_loader: Type[DirectoryDataLoader],
    file_loader: Type[FileDataLoader],
    data_path: Path,
) -> None:
    """
    Process simulation data using the provided simulation loaders

    Parameters:
    -----------
    directory_loader (Type[DirectoryDataLoader]): class to load directory
    file_loader (Type[FileDataLoader]): class to load file
    data_path (Path): Path to the simulation data directory
    """
    # --- Load simulation data --- #
    parent_directory = data_path.resolve().parent.name
    logger.info(f"Finding simulation data in {parent_directory}")
    loader = directory_loader(
        file_loader=file_loader,
        source=parent_directory,
        folder=data_path,
    )

    # Configure loader for OpenFOAM data stracture
    if isinstance(loader, OpenFOAMLinesLoader):
        loader.subfolder = FilePaths.LINES_SUBFOLDER  # type: ignore[arg-type]
        loader.plane_set = plane_set  # type: ignore[arg-type]

    else:
        raise TypeError(f"Unsupported loader type: {type(loader)}. ")

    # Mapping data files into planes
    # BAD practice: This affects the plane_set passed in
    loader.load(data_path)
