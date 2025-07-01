# README for Test Suite

## Overview

This test suite is designed to test the functionality of the postprocess4validation package, focusing on the core and quantitative modules. The tests cover data structures, loading mechanisms, metrics computation, and analysis pipelines.

## Structure

- `tests/` - Main test directory
  - `conftest.py` - Pytest fixtures for data loading
  - `test_core.py` - Tests for core module functionality
  - `test_quantitative.py` - Tests for quantitative analysis functionality
  - `static/` - Static test data
    - `experiment_data/` - Experiment data files
    - `simulation_data/` - Simulation data files

## Running the Tests

Due to the package's import structure, you'll need to install the package in development mode before running the tests:

```bash
cd /path/to/app
pip install -e .
pip install .[dev]
```

Then run the tests with:

```bash
pytest -v tests/
```

## Test Coverage

- **Core Module Tests**:
  - PointData creation and field access
  - DataSet operations and consistency checks
  - CSV data loading functionality
  - Integration tests for data loading

- **Quantitative Module Tests**:
  - Metrics computation (NMSE, MG, GV)
  - Safe array conversion
  - Dataset comparison functionality
  - Analysis pipeline integration
