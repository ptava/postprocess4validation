from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)

class FilePaths:
    PATH_TO_EXP_FILE = Path.cwd() / "expData.csv"
    OUTPUT_DIR = "preprocess"
    FILE_PROBES = "FOprobes"
    FILE_LINES = "FOlines"

class DefaultValues:
    FLOW_DIR = "X"
    NUMBER_OF_POINTS = 500
    MAX_X = 100.0
    MAX_Y = 100.0
    MAX_Z = 100.0
    MIN_X = -100.0
    MIN_Y = -100.0
    MIN_Z = -100.0
    PROBES_FORMAT = "csv"
    LINES_FORMAT = "raw"
