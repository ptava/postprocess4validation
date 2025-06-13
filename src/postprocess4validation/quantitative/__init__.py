"""
Quantitative analysis module for postprocess4validation package.

This module provides tools for quantitative analysis of OpenFOAM simulation results
compared to experiment data. It calculates statistical metrics and visualizes
the results.
"""

from .cli import main
from .computations import compute_metrics
from .analysis import run_quantitative_analysis
from .visualization import (
    define_2Dplot_storage,
    store_2Dplot_data,
    create_2Dplot,
    define_3Dplot_storage,
    store_3Dplot_data,
    create_3Dplot,
)
from .zoom import add_interactive_lens
from .probes_data_loader import (
    ProbesLoader,
    OpenFOAMProbesLoader,
)

__all__ = [
    'main',
    'compute_metrics',
    'run_quantitative_analysis',
    'define_2Dplot_storage',
    'store_2Dplot_data',
    'create_2Dplot',
    'define_3Dplot_storage',
    'store_3Dplot_data',
    'create_3Dplot',
    'add_interactive_lens',
    'OpenFOAMProbesLoader',
    'ProbesLoader',
]
