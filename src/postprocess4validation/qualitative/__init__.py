"""
Qualitative analysis module for postprocess4validation package.

This module provides tools for qualitative analysis of OpenFOAM simulation results
compared to experiment data. It plots all possible slices of the domain based on
the flow direction, points in the dataset, and available lines data.
"""

from .cli import main
from .lines_data_loader import OpenFOAMLinesLoader, LinesDataLoader
from .analysis import run_qualitative_analysis
from .visualization import create_plots

__all__ = [
    "main",
    "OpenFOAMLinesLoader",
    "LinesDataLoader",
    "run_qualitative_analysis",
    "create_plots",
]
