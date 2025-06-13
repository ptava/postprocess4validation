from argparse import ArgumentParser, Namespace

from ..core import LoaderRegistry, LoaderKind, file_path
from .utils import FilePaths, DefaultValues

def parser() -> Namespace:
    """
    Parse command line arguments for pre-processing operations

    Returns:
    --------
    argparse.Namespace: Parsed command line arguments
    """
    parser = ArgumentParser(
        description="Pre-process the data for creating function objects files"
    )

    parser.add_argument(
        "--flow-dir", "-d",
        required=False,
        default=DefaultValues.FLOW_DIR,
        choices=["X", "Y", "Z"],
        help=(
            "Specify the direction of the flow.\n"
            "Default is 'X'."
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
        "--probes", "-p",
        action="store_true",
        default=False,
        help="Create probes file"
    )

    parser.add_argument(
        "--lines", "-l",
        action="store_true",
        default=False,
        help="Create lines file"
    )

    parser.add_argument(
        "--n-points",
        type=int,
        default=DefaultValues.NUMBER_OF_POINTS,
        help=(
            "Number of points to sample along the lines.\n"
            "Default is 500."
        ),
    )

    parser.add_argument(
        "--probes-file",
        type=str,
        default=FilePaths.FILE_PROBES,
    )

    parser.add_argument(
        "--probes-format",
        type=str,
        default=DefaultValues.PROBES_FORMAT,
    )

    parser.add_argument(
        "--lines-format",
        type=str,
        default=DefaultValues.LINES_FORMAT,
    )

    parser.add_argument(
        "--max-limits",
        metavar=('X', 'Y', 'Z'),
        type=float,
        nargs=3,
        default=(DefaultValues.MAX_X, DefaultValues.MAX_Y, DefaultValues.MAX_Z),
        help=(
            "Maximum limits for the lines in the format: x y z.\n"
            "Default is 100.0 100.0 100.0."
        ),
    )

    parser.add_argument(
        "--min-limits",
        metavar=('X', 'Y', 'Z'),
        type=float,
        nargs=3,
        default=(DefaultValues.MIN_X, DefaultValues.MIN_Y, DefaultValues.MIN_Z),
        help=(
            "Minimum limits for the lines in the format: x y z.\n"
            "Default is -100.0 -100.0 -100.0."
        ),
    )

    parser.add_argument(
        "--lines-file",
        type=str,
        default=FilePaths.FILE_LINES,
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
        "--loader",
        choices=LoaderRegistry.get_all(LoaderKind.FILE),
        default=LoaderRegistry.get('CSV'),
        help="Specify the file loader for experiment data."
    )

    return parser.parse_args()


