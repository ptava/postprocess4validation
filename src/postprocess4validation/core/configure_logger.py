from logging import basicConfig, DEBUG, INFO, WARNING

def configure_logger(verbose: bool = False, debug: bool = False) -> None:
    level = DEBUG if debug else INFO if verbose else WARNING
    basicConfig(
        level=level,
        format="%(levelname)s - %(message)s"
    )
