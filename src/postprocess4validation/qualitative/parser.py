from argparse import ArgumentParser, Namespace
from itertools import product

from ..core import (
    LoaderRegistry,
    LoaderKind,
    file_path,
    dir_path,
    Info,
    DefaultValues as core_defaults,
)
from .utils import FilePaths, PlotConstants, DefaultValues


def parser() -> Namespace:
    """
    Parse command line arguments for the qualitative analysis module.

    Returns:
    --------
    argparse.Namespace: Parsed command line arguments.
    """
    parser = ArgumentParser(
        description="Qualitative analysis of simulation data against experiment data."
    )

    parser.add_argument(
        "--flow-dir", "-d",
        required=False,
        default=core_defaults.FLOW_DIR,
        choices=["X", "Y", "Z"],
        help=(
            "Specify the direction of the flow.\n"
            "Default is 'x'."
        ),
    )

    parser.add_argument(
        "--single",
        type=dir_path,
        required=False,
        help=(
            "Specify the path/to/postProcessing when using single mode.\n"
            "Required if --single is set."
        ),
    )

    parser.add_argument(
        "--time-folder", "-t",
        type=str,
        required=False,
        default=None,
        help=(
            "Specify time folder of the simulations data (common to all).\n"
            "Default is latest time folder. Not supported entirely yet."
        ),
    )

    parser.add_argument(
        "--exp-data", "-e",
        type=file_path,
        required=False,
        default=FilePaths.PATH_TO_EXP_FILE,
        help=(
            f"Specify relative path to experiment dataset.\n"
            f"Default is '{FilePaths.PATH_TO_EXP_FILE}'."
        ),
    )

    parser.add_argument(
        "--output-folder",
        type=dir_path,
        required=False,
        default=FilePaths.OUTPUT_FOLDER,
        help=(
            "Specify relative path to output directory.\n"
            "Default is current directory."
        ),
    )

    parser.add_argument(
        "--author",
        type=str,
        default=Info.USER,
        help=(
            "Author name to include in the statistics file header.\n"
            "(defaults to system user)."
        ),
    )

    parser.add_argument(
        "--lab",
        type=str,
        default=Info.LAB,
        help="Reference laboratory name to include in the statistics file header."
    )

    parser.add_argument(
        "--school",
        type=str,
        default=Info.SCHOOL,
        help="School name to include in the statistics file header."
    )

    parser.add_argument(
        "--save-only", "-s",
        action="store_true",
        default=False,
        help="Save plot to file without displaying it."
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable INFO-level logging output"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable DEBUG-level logging output"
    )

    parser.add_argument(
        "--loader-exp",
        choices=LoaderRegistry.get_all(LoaderKind.FILE),
        default=LoaderRegistry.get('CSV'),
        help="Specify the file loader for experiment data."
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help="Enable interactive feature in the plot."
    )

    parser.add_argument(
        "--zoom",
        action="store_true",
        default=False,
        help=(
            "Enable interactive lens for 2D plot. Not yet implemented because"
            "add_interactive_lens supports now inly log-log axes"
        )
    )

    parser.add_argument(
        "--figure-hsize",
        type=float,
        default=PlotConstants.PLOT_SIZE[0],
        help=(
            "Specify the horizontal size of the figure in inches.\n"
            f"Default is {PlotConstants.PLOT_SIZE[0]}."
        ),
    )

    parser.add_argument(
        "--figure-vsize",
        type=float,
        default=PlotConstants.PLOT_SIZE[1],
        help=(
            "Specify the vertical size of the figure in inches.\n"
            f"Default is {PlotConstants.PLOT_SIZE[1]}."
        ),
    )

    parser.add_argument(
        "--stl",
        type=file_path,
        required=False,
        default=None,
        help=(
            "Specify the path to the STL file for 3D plot.\n"
            "Default is None."
        ),
    )

    parser.add_argument(
        "--min-lines",
        type=int,
        required=False,
        default=DefaultValues.MIN_LINES_PER_PLANE,
        help=(
            "Specify the minimum number of lines with data per plane.\n"
            "Default one line is sufficient to make the plot."
        )
    )

    parser.add_argument(
        "--loader-sim",
        type=LoaderRegistry.loader_pair,
        choices=[f"{a}:{b}" for a, b in product(
            LoaderRegistry.get_all(LoaderKind.DIRECTORY),
            LoaderRegistry.get_all(LoaderKind.FILE)
        )],
        default=[
            LoaderRegistry.get('OpenFOAMLines'),
            LoaderRegistry.get('RAWLines'),
        ],
        help=(
            "Specify the loader for simulation data in the form of\n"
            "'DirectoryDataLoader:FileDataLoader'."
        ),
    )

    return parser.parse_args()
