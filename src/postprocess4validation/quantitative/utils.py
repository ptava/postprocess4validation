"""
Constants and utility functions for the quantitative analysis module.

This module provides common constants and utility functions used across
the quantitative analysis package.
"""
from typing import List, Union, Optional, Dict, Any
from pathlib import Path
from numpy import ndarray, asarray, isnan, isinf, any
from logging import (
    getLogger,
    INFO,
    CRITICAL,
    StreamHandler, 
    FileHandler, 
    Formatter
)


logger = getLogger(__name__)
getLogger('matplotlib.font_manager').setLevel(CRITICAL)
getLogger('matplotlib.ticker').setLevel(CRITICAL)

class MetricNames:
    """Names of metrics used in quantitative analysis."""
    NMSE = "NMSE"  # Normalized Mean Squared Error
    MG = "MG"      # Mean Geometric Bias
    GV = "GV"      # Geometric Variance
    NRE = "NRE"    # Normalised Relative Error

    @classmethod
    def get_all(cls) -> List[str]:
        """Return a list of all metric names."""
        return [cls.NMSE, cls.MG, cls.GV]

class PlotConstants:
    """Constants related to plotting and visualization."""
    MARGIN = 1.15
    LINEWIDTH = 0.85
    INSET_SIZE = "70%"
    LENS_BOX = (0.05, 0.37, 0.6, 0.6)
    PLOT2D_FIGSIZE = (8, 6) # Width, Height
    DELTA_LOG = 0.1
    PLOT3D_FIELD = MetricNames.NRE
    PLOT3D_FIGSIZE = (6, 6) # Width, Height
    PLOT3D_FIGMAXHEIGHT = 14 # Maximum height of the 3D plot
    PLOT3D_EL= 35.0 # Elevation
    PLOT3D_AZ = -135.0 # Azimuth
    PLOT3D_CMAP = "RdBu_r"
    MAX_COLS = 3


class FilePaths:
    """Default file and directory paths."""
    PATH_TO_EXP_FILE = Path.cwd() / "expData.csv"
    STATS_FILENAME = "statistics.csv"
    PLOT2D_FILENAME = "plot.png"
    PLOT3D_FILENAME = "3d_plot.png"
    PROBES_SUBFOLDER = "probes"

class ValidationConstants:
    """Constants used for validation."""
    ZERO_THRESHOLD = 1e-10  # Threshold for considering a value as zero

def safe_array_conversion(data: Any, dtype: Any = float) -> ndarray:
    """
    Safely convert data to a numpy array with validation.
    
    Parameters
    ----------
    data (Any): data to convert
    dtype (Any, optional): data type for the array, by default float
        
    Returns
    -------
    ndarray: converted numpy array
        
    Raises
    ------
    TypeError: if the data cannot be converted to a numpy array
    ValueError: if the resulting array contains NaN or Inf values
    """
    try:
        arr = asarray(data, dtype=dtype)
    except (ValueError, TypeError) as e:
        raise TypeError(f"Failed to convert data to numpy array: {e}")
    
    # Check for NaN or Inf values
    if any(isnan(arr)) or any(isinf(arr)):
        raise ValueError("Data contains NaN or Inf values")
    
    # Check for empty array
    if arr.size == 0:
        raise ValueError("Data cannot be empty")
        
    return arr


def format_nested_dict(data: Dict, indent: int = 0) -> str:
    """
    Format a nested dictionary as a string with indentation.
    
    Parameters
    ----------
    data (Dict): dictionary to format
    indent (int, optional): initial indentation level, by default 0
        
    Returns
    -------
    str: formatted string representation of the dictionary
    """
    result = []
    spaces = ' ' * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            result.append(f"{spaces}{key}:")
            result.append(format_nested_dict(value, indent + 2))
        else:
            result.append(f"{spaces}{key}: {value}")
            
    return '\n'.join(result)

def setup_logging(
    level: int = INFO,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True
) -> None:
    """
    Configure logging for the application.
    """
    root_logger = getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = Formatter('%(levelname)s: %(message)s')
    
    # Add console handler if requested
    if console:
        console_handler = StreamHandler()
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = FileHandler(log_path)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_path}")
        except Exception as e:
            logger.error(f"Failed to set up file logging: {e}")

