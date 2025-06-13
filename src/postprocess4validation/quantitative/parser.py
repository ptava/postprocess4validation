from argparse import ArgumentParser, Namespace
from itertools import product

from ..core import (
    Info,
    LoaderKind,
    LoaderRegistry,
    dir_path,
    file_path,
)
from .utils import FilePaths

def parser() -> Namespace:
    """
    Parse command line arguments.
    
    Returns
    -------
    argparse.Namespace: parsed arguments
    """
    parser = ArgumentParser(
        description="Post-process OpenFOAM data for validation: quantitative analysis."
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
        "--exp-data",
        type=file_path,
        required=False,
        default=FilePaths.PATH_TO_EXP_FILE,
        help=(
            f"Specify relative path to experiment dataset.\n"
            f"Default is '{FilePaths.PATH_TO_EXP_FILE}'."
        ),
    )

    parser.add_argument(
        "--time-folder",
        type=str,
        required=False,
        default=None,
        help=(
            "Specify time folder of the simulations data (common to all).\n"
            "Default is latest time folder."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=dir_path,
        required=False,
        default=Info.OUTPUT_DIR,
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
        "--interactive",
        action="store_true",
        default=False,
        help="Enable interactive lens for 2D plot"
    )
    
    parser.add_argument(
        "--save-only",
        action="store_true",
        default=False,
        help="Save plot to file without displaying it."
    )
    
    parser.add_argument(
        "--verbose",
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
        "--loader-sim",
        type=LoaderRegistry.loader_pair,
        choices=[f"{a}:{b}" for a, b in product(
            LoaderRegistry.get_all(LoaderKind.DIRECTORY),
            LoaderRegistry.get_all(LoaderKind.FILE)
        )],
        default=[
            LoaderRegistry.get('OpenFOAMProbes'),
            LoaderRegistry.get('CSVProbes')
        ],
        help=(
            "Specify the loader for simulation data in the form of\n"
            "'DirectoryDataLoader:FileDataLoader'."
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

    return parser.parse_args()


