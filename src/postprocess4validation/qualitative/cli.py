"""
Command Line Interface (CLI) for the qualitative analysis module.

This script provides a command-line interface to run the qualitative analysis
pipeline, comparing simulation data against experiment data, generating plots
for all the possible slices of the domain.

Based on the flow direction, points in the dataset, and available lines data,
it generates all the possible plots in two orthogonal planes.

Example: 
    Flow direction = 'X'
    Planes on 'XY' and 'XZ'
"""
from typing import List
from pathlib import Path

from ..core import (
    DataSet,
    configure_logger,
    find_postProcessing,
)
from .parser import parser
from .utils import logger, FilePaths
from .analysis import run_qualitative_analysis
from .visualization import create_plots


def main() -> int:
    """
    Main function to run the qualitative analysis pipeline.
    """
    try:
        # --- Parse command line arguments --- #
        args = parser()

        # --- Configure logger --- #
        configure_logger(args.verbose, args.debug)

        # --- Load experiment data --- #
        # TO DO: class implementation to be changed (loader that can pass also
        # input file path and the call load without arguments)
        experiment_loader = args.loader_exp(source="experiment")
        experiment_dataset: DataSet = experiment_loader.load(args.exp_data)

        # --- Process experiment data --- #
        logger.info(f"Processing experiment data from: {args.exp_data}")
        planes = experiment_dataset.points_to_planes()

        # --- Initialise output file --- #
        plot_file = args.output_folder / FilePaths.PLOT_FILENAME
        plot_flag = False

        # --- Collect paths of data files --- #
        simulations_data_folders: List[Path]
        if args.single:
            logger.info(f"Single simulation mode: {args.single}")
            simulations_data_folders = [args.single]
        else:
            logger.info("Multiple simulation mode")
            plot_flag = True
            simulations_data_folders = find_postProcessing()
            if not simulations_data_folders:
                logger.error(
                    "No postProcessing directories found."
                    "Use --single to specify a path."
                )
                return 1

        # --- Process each simulation data --- #
        run_qualitative_analysis(
            simulations_data_folders,
            plane_set=planes,
            directory_loader=args.loader_sim[0],
            file_loader=args.loader_sim[1],
        )

        logger.info("Processing completed, generating plots... ")

        # --- Generate plots --- #
        create_plots(
            planes=planes,
            file_path=plot_file,
            save_only=args.save_only,
            last_timestep_only=plot_flag,
            interactive=args.interactive,
            geometry=args.stl,
            min_lines_per_plane=args.min_lines
        )

        logger.info("Processing completed successfully")

        return 0
    except Exception as e:
        logger.error(f"CLI: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
