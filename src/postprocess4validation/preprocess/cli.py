from .parser import parser
from .utils import logger
from .create_files import create_probes_file, create_lines_file
from ..core import configure_logger


def main() -> int:
    """
    Main function to run the preprocessing operations.
    """
    try:
        # --- Parse command line arguments ---
        args = parser()

        # --- Configure logger --- #
        configure_logger(args.verbose, args.debug)

        # --- Load input data ---
        loader = args.loader(source="experiment")
        data = loader.load(args.exp_data)

        # --- Create files ---
        if not args.lines:
            logger.info("CLI: Creating probes function object file...")
            create_probes_file(
                file_path=args.probes_file,
                fields=data.fields,
                coordinates=data.get_all_coordinates(),
                format=args.probes_format
            )

        if not args.probes:
            logger.info("CLI: Creating lines function object file...")
            planes = data.points_to_planes(args.flow_dir)
            create_lines_file(
                file_path=args.lines_file,
                planes=planes,
                fields=data.fields,
                format=args.lines_format,
                min=tuple(args.min_limits),
                max=tuple(args.max_limits),
                n_points=args.n_points,
            )

        logger.info("CLI: Preprocessing completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"CLI: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

