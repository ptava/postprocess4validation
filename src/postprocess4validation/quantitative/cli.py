"""
Command Line Interface (CLI) for the quantitative analysis module.

This script provides a command-line interface to run the quantitative analysis
pipeline, comparing simulation data against experiment data, computing metrics,
and generating visualizations.
"""
from __future__ import annotations
from warnings import filterwarnings
from typing import List
from pathlib import Path

from ..core import (
    DataSet,
    find_postProcessing,
    initialise_metrics_file,
    configure_logger,
)
from .parser import parser
from .analysis import run_quantitative_analysis
from .visualization import (
    define_2Dplot_storage,
    create_2Dplot,
    define_3Dplot_storage,
    create_3Dplot,
)
from .utils import (
    logger,
    FilePaths,
)

# Convert specific warning to exception
filterwarnings(
    "error",
    message=".*FigureCanvasAgg is non-interactive.*",
    category=UserWarning
)

# Suppress specific warnings
filterwarnings(
    "ignore",
    category=UserWarning,
    message=r"(.*tight_layout.*|.*3d coordinates not supported.*)"
)


def main() -> int:
    """
    Main function to perform quantitative analysis of points data.

    This function:
    1. Parses command line arguments
    2. Loads experiment dataset
    3. Initializes output files
    4. Creates visualization plot
    5. Processes simulation data (single or multiple)
    6. Finalizes and displays the plot
    
    Returns
    -------
    int: exit code
    """
    try:
        # --- Parse arguments --- #
        args = parser()

        # --- Set up logging --- #
        configure_logger(args.verbose, args.debug)

        # --- Load experiment data --- #
        experiment_loader = args.loader_exp(source="experiment")
        experiment_dataset : DataSet = experiment_loader.load(args.exp_data)

        # --- Initialise output file --- #
        statistics_file = args.output_dir / FilePaths.STATS_FILENAME
        plot2D_file = args.output_dir / FilePaths.PLOT2D_FILENAME
        plot3d_file = args.output_dir / FilePaths.PLOT3D_FILENAME

        logger.info(f"Initializing output file {statistics_file}")
        initialise_metrics_file(
            path = statistics_file,
            author = args.author,
            lab = args.lab,
            school = args.school,
        )

        # --- Initialize plots requirements --- #
        plot_flag = False
        data2D = define_2Dplot_storage() 
        data3d = define_3Dplot_storage(experiment_dataset)

        # -- Run analysis --- #
        sim_paths: List[Path]
        if args.single:
            logger.info( f"Single simulation mode: {args.single}")
            sim_paths = [args.single]
        else:
            logger.info("Multiple simulation mode")
            plot_flag = True
            sim_paths = find_postProcessing()
            if not sim_paths:
                logger.error(
                    "No postProcessing directories found."
                    "Use --single to specify a path."
                )
                return 1
                
        for sim_path in sim_paths:
            try:
                logger.info(f"Processing simulation: {sim_path.resolve()}")
                run_quantitative_analysis(
                    directory_loader=args.loader_sim[0],
                    file_loader=args.loader_sim[1],
                    output_file=statistics_file,
                    ref_dataset=experiment_dataset,
                    data_storage_2D=data2D,
                    data_storage_3D=data3d,
                    data_path=sim_path,
                    last_time_only=plot_flag,
                    time=args.time_folder,
                )
            except Exception as e:
                logger.error(f"Unexpected error during quantitative analysis: {e}")

        # Finalize plots
        logger.info("Processing completed, finalizing plots... ")
        
        # Finalise the plots (show or save)
        create_2Dplot(
            data_storage=data2D,
            file_path=plot2D_file,
            save_only=args.save_only,
            interactive=args.interactive,
        )
        create_3Dplot(
            data_storage=data3d,
            file_path=plot3d_file,
            save_only=args.save_only,
            geometry=args.stl,
        )
            
        logger.info("Plotting completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"CLI: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
