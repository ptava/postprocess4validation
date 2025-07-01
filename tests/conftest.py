"""
Pytest configuration and fixtures for the postprocess4validation test suite.

This module provides fixtures for loading experiment and simulation data
that can be reused across test modules.
"""
import pytest
from pathlib import Path
import os
import sys

# Add the parent directory to sys.path to make the app module importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from postprocess4validation.core import (
    CSVDataLoader,
)
from postprocess4validation.quantitative import (
    OpenFOAMProbesLoader,
    ProbesLoader,
)

# Define paths relative to this file
TEST_DIR = Path(__file__).parent
STATIC_DIR = TEST_DIR / "static"
EXPERIMENT_DATA_DIR = STATIC_DIR / "experiment_data"
SIMULATION_DATA_DIR = STATIC_DIR / "simulation_data" / "simulation_data"


@pytest.fixture(scope="session")
def experiment_data_path():
    """Return the path to the experiment data CSV file."""
    exp_file = EXPERIMENT_DATA_DIR / "expData.csv"
    if not exp_file.exists():
        pytest.fail(f"Experiment data file not found: {exp_file}")
    return exp_file


@pytest.fixture(scope="session")
def simulation_data_path():
    """Return the path to the simulation data directory."""
    if not SIMULATION_DATA_DIR.exists():
        pytest.fail(f"Simulation data directory not found: {SIMULATION_DATA_DIR}")
    return SIMULATION_DATA_DIR


@pytest.fixture(scope="session")
def experiment_dataset(experiment_data_path):
    """
    Load experiment data into a DataSet object.
    
    Returns:
        DataSet: Dataset containing experiment data
    """
    try:
        loader = CSVDataLoader(source="experiment")
        dataset = loader.load(experiment_data_path)
        return dataset
    except Exception as e:
        pytest.fail(f"Failed to load experiment data: {e}")


@pytest.fixture(scope="session")
def simulation_probes_paths(simulation_data_path):
    """
    Return a list of paths to simulation probe directories.
    
    Returns:
        list: List of Path objects pointing to probe directories
    """
    probe_dirs = []
    try:
        # Look for postProcessing directories
        for root, dirs, _ in os.walk(simulation_data_path):
            for dir_name in dirs:
                if dir_name == "postProcessing":
                    post_proc_dir = Path(root) / dir_name
                    # Check for probes subdirectory
                    for subdir in post_proc_dir.iterdir():
                        if subdir.is_dir() and "probes" in subdir.name.lower():
                            probe_dirs.append(subdir)
        
        if not probe_dirs:
            pytest.fail("No probe directories found in simulation data")
        
        return probe_dirs
    except Exception as e:
        pytest.fail(f"Failed to locate simulation probe directories: {e}")


@pytest.fixture(scope="session")
def simulation_dataset(simulation_probes_paths):
    """
    Load simulation data from the first available probe directory.
    
    Returns:
        DataSet: Dataset containing simulation data
    """
    if not simulation_probes_paths:
        pytest.fail("No simulation probe paths available")
    
    try:
        probe_dir = simulation_probes_paths[0]
        # Find the parent directory (case name)
        case_name = probe_dir.parent.parent.name
        
        # Find time folders
        time_folders = [d for d in probe_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
        if not time_folders:
            pytest.fail(f"No time folders found in {probe_dir}")
        
        # Use the latest time folder
        latest_time = sorted(time_folders, key=lambda x: float(x.name))[-1]
        
        # Create and configure the loader
        loader = OpenFOAMProbesLoader(
            file_loader=ProbesLoader,
            folder=probe_dir.parent,  # postProcessing directory
            source=case_name,
            subfolder=probe_dir.name,
            time=latest_time.name
        )
        
        # Load the data
        dataset = loader.load(probe_dir.parent)
        return dataset
    except Exception as e:
        pytest.fail(f"Failed to load simulation data: {e}")


@pytest.fixture(scope="session")
def all_simulation_datasets(simulation_probes_paths):
    """
    Load simulation data from all available probe directories.
    
    Returns:
        dict: Dictionary mapping case names to DataSet objects
    """
    if not simulation_probes_paths:
        pytest.fail("No simulation probe paths available")
    
    datasets = {}
    
    for probe_dir in simulation_probes_paths:
        try:
            # Find the parent directory (case name)
            case_name = probe_dir.parent.parent.name
            
            # Find time folders
            time_folders = [d for d in probe_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
            if not time_folders:
                continue
            
            # Use the latest time folder
            latest_time = sorted(time_folders, key=lambda x: float(x.name))[-1]
            
            # Create and configure the loader
            loader = OpenFOAMProbesLoader(
                file_loader=ProbesLoader,
                folder=probe_dir.parent,  # postProcessing directory
                source=case_name,
                subfolder=probe_dir.name,
                time=latest_time.name
            )
            
            # Load the data
            dataset = loader.load(probe_dir.parent)
            datasets[case_name] = dataset
        except Exception as e:
            print(f"Warning: Failed to load simulation data for {probe_dir}: {e}")
    
    if not datasets:
        pytest.fail("Failed to load any simulation datasets")
    
    return datasets
