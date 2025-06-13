from pathlib import Path
from logging import getLogger

logger = getLogger(__name__)

class FilePaths:
    """Default file and directory paths."""
    _current_dir = Path.cwd()
    PATH_TO_EXP_FILE = _current_dir / "expData.csv"
    OUTPUT_FOLDER = _current_dir
    LINES_SUBFOLDER = "lines"
    PLOT_FILENAME = "plot_lines.png"

class PlotConstants:
    PLOT_SIZE = (14.0, 6.0)  # Width, Height in inches
    FIGURE_MAXHEIGHT = 14.0
    FIGURE_MAXCOLUMNS = 1
    SLIDER_POSITION = (0.4, 0.02, 0.3, 0.03)  # (left, bottom, width, height)

class DefaultValues:
    FIELD_SCALE = 0.005
    MIN_LINES_PER_PLANE = 1


