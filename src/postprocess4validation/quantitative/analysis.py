from __future__ import annotations
from typing import Dict, Type, Optional, Any
from pathlib import Path

from ..core import (
    DataSet,
    write_metrics,
    DirectoryDataLoader,
    FileDataLoader,
)
from .probes_data_loader import OpenFOAMProbesLoader
from .computations import compute_metrics
from .visualization import store_2Dplot_data, store_3Dplot_data
from .utils import (
    logger,
    FilePaths,
)


def run_quantitative_analysis(
    directory_loader: Type[DirectoryDataLoader],
    file_loader: Type[FileDataLoader],
    output_file: Path, 
    ref_dataset: DataSet, 
    data_storage_2D: Dict[str, Any],
    data_storage_3D: Dict[str, Any],
    data_path: Path,
    last_time_only: bool = False,
    time: Optional[str] = None
) -> Dict:
    """
    Run quantitative analysis on simulation data.
    
    This function:
    1. Porcesses simulation data usign the provided simulation loaders
    2. Computes metrics comparing simulation with reference data
    3. Writes metrics to output file
    4. Updates visualization plot
    5. Creates a 3D plot associated with the simulation data
    
    Parameters
    ----------
    directory_loader (Type[DirectoryDataLoader]): Class to load directory
    file_loader (Type[FileDataLoader]): Class to load file data
    output_file (Path): Path to the output file where metrics will be written
    ref_dataset (DataSet): Reference dataset for comparison
    ax (AxesWithPlotData): Axes object for 2D plot
    ax3d (AxesWithPlotData): Axes object for 3D plot
    data_path (Path): Path to the simulation data directory
    last_time_only (bool): Flag to hangle single or multiple simulations plots
    time (Optional[str]): Specific time step to process; if None, latest time
        folder is used

    Returns
    -------
    Dict: dictionary containing the computed metrics
    """
        
    # Find and process simulation data
    try:
        parent_directory = data_path.resolve().parent.name
        logger.info(f"Finding simulation data in {parent_directory}")

        loader = directory_loader(
            file_loader=file_loader,
            source=parent_directory,
            folder=data_path,
        )

        # Configure loader for OpenFOAM data structure
        if isinstance(loader, OpenFOAMProbesLoader):
            loader.subfolder = FilePaths.PROBES_SUBFOLDER # type: ignore
            loader.time = time # type: ignore
        else:
            raise TypeError(f"Unsupported loader type: {type(loader)}") 

        logger.info(f"Processing data from {data_path} with loader: "
            f"{loader.name}")

        simulation_data: DataSet = loader.load(data_path)
        
    except Exception as e:
        logger.error(f"Failed to process simulation data: {e}")
        raise ValueError(f"Failed to process simulation data: {e}")

    # Perform computations
    try:
        logger.info("Computing metrics")
        results = compute_metrics(ref_dataset, simulation_data)
    except Exception as e:
        logger.error(f"Failed to compute metrics: {e}")
        raise ValueError(f"Failed to compute metrics: {e}")

    # Write to output file
    try:
        logger.info(f"Writing metrics to {output_file}")
        write_metrics(output_file, simulation_data.source, results, last_time_only)
    except Exception as e:
        logger.error(f"Failed to write metrics to file: {e}")
        raise ValueError(f"Failed to write metrics to file: {e}")

    # Fill the plot with the relevant computed metrics
    try:
        logger.info("Updating visualization")
        store_2Dplot_data(data_storage_2D, simulation_data.source, results, last_time_only)
    except Exception as e:
        logger.error(f"Failed to update visualization: {e}")
        raise ValueError(f"Failed to update visualization: {e}")

    try:
        logger.info("Creating 3D subplot")
        store_3Dplot_data(simulation_data, data_storage_3D, last_time_only)

    except Exception as e:
        logger.error(f"Failed to create 3D subplot: {e}")
        raise ValueError(f"Failed to create 3D subplot: {e}")
    return results
