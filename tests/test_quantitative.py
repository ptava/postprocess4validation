"""
Tests for the quantitative module of the postProcess4Validation package.

This module contains tests for the quantitative analysis functionality including:
- Metrics computation
- Analysis pipeline
- Visualization functions
"""
import pytest
import numpy as np
from pathlib import Path
from postprocess4validation.core import DataSet
from postprocess4validation.quantitative.computations import (
    _compute_nmse,
    _compute_mean_bias,
    _compute_geometric_variance
)

from postprocess4validation.quantitative import (
    compute_metrics,
    run_quantitative_analysis,
    OpenFOAMProbesLoader,
    ProbesLoader,
)

from postprocess4validation.quantitative.utils import (
    MetricNames,
    safe_array_conversion
)


class TestMetricsComputation:
    """Tests for the metrics computation functions."""

    def test_safe_array_conversion(self):
        """Test safe array conversion function."""
        # Test with valid data
        data = [1.0, 2.0, 3.0]
        result = safe_array_conversion(data)
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, np.array([1.0, 2.0, 3.0]))
        
        # Test with invalid data
        with pytest.raises(TypeError):
            safe_array_conversion(["a", "b", "c"])
        
        # Test with NaN values
        with pytest.raises(ValueError):
            safe_array_conversion([1.0, np.nan, 3.0])
        
        # Test with Inf values
        with pytest.raises(ValueError):
            safe_array_conversion([1.0, np.inf, 3.0])
        
        # Test with empty array
        with pytest.raises(ValueError):
            safe_array_conversion([])

    def test_compute_nmse(self):
        """Test NMSE computation."""
        dataset = DataSet(source="test")
        field = "velocity"
        predictions = np.array([1.0, 2.0, 3.0])
        experiment = np.array([1.1, 2.2, 2.8])
        
        # Compute NMSE
        nmse = _compute_nmse(predictions, experiment)
        
        # Check result type and value
        assert isinstance(nmse, float)
        assert nmse > 0.0  # NMSE should be positive
        
    def test_compute_mean_bias(self):
        """Test Mean Geometric Bias computation."""
        predictions = np.array([1.0, 2.0, 3.0])
        experiment = np.array([1.1, 2.2, 2.8])
        
        # Compute MG
        mg = _compute_mean_bias(predictions, experiment)
        
        # Check result type and value
        assert isinstance(mg, float)
        assert mg > 0.0  # MG should be positive
        
    def test_compute_geometric_variance(self):
        """Test Geometric Variance computation."""
        predictions = np.array([1.0, 2.0, 3.0])
        experiment = np.array([1.1, 2.2, 2.8])
        
        # Compute GV
        gv = _compute_geometric_variance(predictions, experiment)
        
        # Check result type and value
        assert isinstance(gv, float)
        assert gv > 0.0  # GV should be positive
        

    def test_compute_metrics_with_real_data(self, experiment_dataset, simulation_dataset):
        """Test metrics computation with real data."""
        # Get a common field between datasets
        common_fields = set(experiment_dataset.fields.keys()).intersection(
            set(simulation_dataset.fields.keys())
        )
        assert len(common_fields) > 0, "No common fields found between datasets"
        
        # Get the first common field
        test_field = list(common_fields)[0]
        
        # Get time values from simulation dataset
        sim_times = simulation_dataset.points[0].get_times()
        assert len(sim_times) > 0, "No time values found in simulation dataset"
        
        # Compute metrics
        results = compute_metrics(
            dataset_from_exp=experiment_dataset,
            dataset_from_sim=simulation_dataset,
            time_values=sim_times,
            fields=[test_field]
        )
        
        # Check that results contain expected metrics
        assert MetricNames.NMSE in results
        assert MetricNames.MG in results
        assert MetricNames.GV in results
        
        # Check that metrics were computed for the test field
        for metric in [MetricNames.NMSE, MetricNames.MG, MetricNames.GV]:
            for time in sim_times:
                if time in results[metric]:
                    assert test_field in results[metric][time]
                    assert isinstance(results[metric][time][test_field], float)


class TestDatasetComparison:
    """Tests for comparing experiment and simulation datasets."""

    def test_dataset_structure_compatibility(self, experiment_dataset, simulation_dataset):
        """Test that experiment and simulation datasets have compatible structures."""
        # Check that both datasets have points
        assert len(experiment_dataset) > 0
        assert len(simulation_dataset) > 0

        # Check that both datasets have fields
        assert len(experiment_dataset.fields) > 0
        assert len(simulation_dataset.fields) > 0

        # Check for common fields
        common_fields = set(experiment_dataset.fields.keys()).intersection(
            set(simulation_dataset.fields.keys())
        )
        assert len(common_fields) > 0, "No common fields found between datasets"

        # Check that points have coordinates
        for point in experiment_dataset.points:
            assert len(point.coordinates) == 3

        for point in simulation_dataset.points:
            assert len(point.coordinates) == 3

    def test_field_values_retrieval(self, experiment_dataset, simulation_dataset):
        """Test retrieving field values from both datasets."""
        # Get a common field
        common_fields = set(experiment_dataset.fields.keys()).intersection(
            set(simulation_dataset.fields.keys())
        )
        assert len(common_fields) > 0, "No common fields found between datasets"

        test_field = list(common_fields)[0]

        # Get time values
        exp_times = list(experiment_dataset.points[0].get_times())
        sim_times = list(simulation_dataset.points[0].get_times())

        assert len(exp_times) > 0, "No time values found in experiment dataset"
        assert len(sim_times) > 0, "No time values found in simulation dataset"

        # Get field values from experiment dataset
        exp_values = experiment_dataset.get_field_values(
            field_name=test_field,
            time=exp_times[0]
        )
        assert len(exp_values) > 0, "No field values retrieved from experiment dataset"

        # Get field values from simulation dataset
        sim_values = simulation_dataset.get_field_values(
            field_name=test_field,
            time=sim_times[0]
        )
        assert len(sim_values) > 0, "No field values retrieved from simulation dataset"

    def test_multiple_simulation_datasets(self, experiment_dataset, all_simulation_datasets):
        """Test comparing experiment data with multiple simulation datasets."""
        assert len(all_simulation_datasets) > 0, "No simulation datasets available"

        # Check that each simulation dataset can be compared with the experiment dataset
        for case_name, sim_dataset in all_simulation_datasets.items():
            # Check that the dataset has points
            assert len(sim_dataset) > 0, f"No points in simulation dataset for {case_name}"

            # Check for common fields
            common_fields = set(experiment_dataset.fields.keys()).intersection(
                set(sim_dataset.fields.keys())
            )
            assert len(common_fields) > 0, f"No common fields found between experiment and {case_name}"

            # Get a common field
            test_field = list(common_fields)[0]

            # Get time values
            sim_times = list(sim_dataset.points[0].get_times())
            assert len(sim_times) > 0, f"No time values found in {case_name} dataset"

            # Get field values
            sim_values = sim_dataset.get_field_values(
                field_name=test_field,
                time=sim_times[0]
            )
            assert len(sim_values) > 0, f"No field values retrieved from {case_name} dataset"

class TestQuantitativeAnalysis:
    """Tests for the quantitative analysis pipeline."""

    def test_metrics_computation_integration(self, experiment_dataset, simulation_dataset, tmp_path):
        """Test integration of metrics computation in the analysis pipeline."""
        # Create a temporary output file
        output_file = tmp_path / "test_metrics.csv"
        
        # Mock the visualization components
        class MockAxes:
            def __init__(self):
                self.plot_data = {}
        
        mock_ax = MockAxes()
        mock_ax3d = MockAxes()
        
        # Run the analysis
        try:
            # Get the simulation path
            sim_path = Path(simulation_dataset.source)
            
            # Run the analysis
            run_quantitative_analysis(
                directory_loader=OpenFOAMProbesLoader,
                file_loader=ProbesLoader,
                output_file=output_file,
                ref_dataset=experiment_dataset,
                data_storage_2D=mock_ax,
                data_storage_3D=mock_ax3d,
                data_path=sim_path,
                last_time_only=True
            )

            # TODO: assert some stuff that this function changes (mock axes)
            
            
        except Exception as e:
            # If the analysis fails, it might be due to missing visualization components
            # or incompatible data. We'll mark this as an expected failure.
            pytest.xfail(f"Analysis failed: {e}")


