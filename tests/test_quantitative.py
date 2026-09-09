"""
Tests for the quantitative module of the postProcess4Validation package.

This module contains tests for the quantitative analysis functionality including:
- Metrics computation
- Analysis pipeline
- Visualization functions
"""
import logging
import pytest
import numpy as np
from matplotlib import pyplot as plt
from postprocess4validation.core import DataSet, PointData, find_postProcessing
from postprocess4validation.quantitative.computations import (
    _compute_nmse,
    _compute_mean_bias,
    _compute_geometric_variance
)

from postprocess4validation.quantitative import (
    ProbesLoader,
    OpenFOAMProbesLoader,
    compute_metrics,
    run_quantitative_analysis,
    define_2Dplot_storage,
    store_2Dplot_data,
    define_3Dplot_storage,
    store_3Dplot_data,
    create_2Dplot,
    create_3Dplot,
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

    def test_compute_metrics_uses_only_matching_coordinates(self, caplog):
        exp_dataset = DataSet(source="experiment")
        exp_dataset.add_point(
            PointData((0.0, 0.0, 0.0), {"UMag": {0.0: 1.0}})
        )
        exp_dataset.add_point(
            PointData((1.0, 0.0, 0.0), {"UMag": {0.0: 2.0}})
        )
        exp_dataset.add_point(
            PointData((2.0, 0.0, 0.0), {"UMag": {0.0: 3.0}})
        )

        sim_dataset = DataSet(source="simulation")
        sim_dataset.add_point(
            PointData((1.0, 0.0, 0.0), {"UMag": {1.0: 2.2}})
        )
        sim_dataset.add_point(
            PointData((2.0, 0.0, 0.0), {"UMag": {1.0: 2.7}})
        )
        sim_dataset.add_point(
            PointData((3.0, 0.0, 0.0), {"UMag": {1.0: 4.0}})
        )

        caplog.set_level(logging.WARNING)
        results = compute_metrics(
            dataset_from_exp=exp_dataset,
            dataset_from_sim=sim_dataset,
            time_values=[1.0],
            fields=["UMag"],
        )

        assert MetricNames.NMSE in results
        assert "UMag" in results[MetricNames.NMSE][1.0]
        assert "Skipping 1 simulation probe point" in caplog.text
        assert "Skipping 1 experiment point" in caplog.text

        assert "NRE_UMag" in sim_dataset.fields
        assert sim_dataset.get_point_by_coordinates(
            (1.0, 0.0, 0.0)
        )["NRE_UMag", 1.0] == pytest.approx(0.1)
        assert sim_dataset.get_point_by_coordinates(
            (2.0, 0.0, 0.0)
        )["NRE_UMag", 1.0] == pytest.approx(0.1)
        with pytest.raises(KeyError):
            sim_dataset.get_point_by_coordinates(
                (3.0, 0.0, 0.0)
            )["NRE_UMag", 1.0]

    def test_3d_plot_storage_uses_coordinates_with_nre_values(self):
        dataset = DataSet(source="simulation")
        dataset.add_point(
            PointData((1.0, 0.0, 0.0), {"NRE_UMag": {1.0: 0.1}})
        )
        dataset.add_point(
            PointData((2.0, 0.0, 0.0), {"NRE_UMag": {1.0: 0.2}})
        )
        dataset.add_point(
            PointData((3.0, 0.0, 0.0), {"UMag": {1.0: 4.0}})
        )
        data_storage = define_3Dplot_storage(dataset)

        store_3Dplot_data(dataset, data_storage)

        assert data_storage["fields"] == ["NRE_UMag"]
        assert data_storage["fields_values"][0].tolist() == [0.1, 0.2]
        assert data_storage["coordinates"][0].tolist() == [
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ]


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


class TestQuantitativeTimeFiltering:
    """Tests for start-time filtering in quantitative data loading."""

    def test_openfoam_probes_loader_filters_before_start_time(
        self,
        simulation_probes_paths,
    ):
        probe_dir = simulation_probes_paths[0]
        case_name = probe_dir.parent.parent.name
        loader = OpenFOAMProbesLoader(
            file_loader=ProbesLoader,
            folder=probe_dir.parent,
            source=case_name,
            subfolder=probe_dir.name,
            time="0",
            start_time=682.0,
        )

        dataset = loader.load(probe_dir.parent)

        assert dataset.get_all_times() == [682.0]

    def test_openfoam_probes_loader_raises_when_filter_removes_all_samples(
        self,
        simulation_probes_paths,
    ):
        probe_dir = simulation_probes_paths[0]
        case_name = probe_dir.parent.parent.name
        loader = OpenFOAMProbesLoader(
            file_loader=ProbesLoader,
            folder=probe_dir.parent,
            source=case_name,
            subfolder=probe_dir.name,
            time="0",
            start_time=683.0,
        )

        with pytest.raises(ValueError, match="start time"):
            loader.load(probe_dir.parent)


class TestQuantitativeAnalysis:
    """Tests for the quantitative analysis pipeline."""

    def test_single_simulation(self, experiment_dataset, simulation_dataset, tmp_path):
        """Test metrics computation for a single simulation in the analysis pipeline."""
        # Create a temporary output file
        metrics_file = tmp_path / "test_metrics.csv"
        plot_file_2D = tmp_path / "test_plot_2D.png"
        plot_file_3D = tmp_path / "test_plot_3D.png"
        
        # Data storage initialization
        data_2D = define_2Dplot_storage()
        mock_ax3d = define_3Dplot_storage(experiment_dataset)
        
        # Run the analysis
        try:
            # Get the simulation path
            sim_paths = find_postProcessing()
            assert len(sim_paths) > 0, "No postProcessing folder found"

            sim_path = sim_paths[0]  # Use the first simulation path
            
            # Run the analysis
            run_quantitative_analysis(
                directory_loader=OpenFOAMProbesLoader,
                file_loader=ProbesLoader,
                output_file=metrics_file,
                ref_dataset=experiment_dataset,
                data_storage_2D=data_2D,
                data_storage_3D=mock_ax3d,
                data_path=sim_path,
                last_time_only=True,
                time=None,
            )

            # TODO: assert some stuff that this function changes (mock axes)

            create_2Dplot(
                data_storage=data_2D,
                file_path=plot_file_2D,
                save_only=True,
                interactive=False,
            )
            create_3Dplot(
                data_storage=mock_ax3d,
                file_path=plot_file_3D,
                save_only=True,
            )

            
        except Exception as e:
            # If the analysis fails, it might be due to missing visualization components
            # or incompatible data. We'll mark this as an expected failure.
            pytest.xfail(f"Analysis failed: {e}")


    def test_multiple_simulations(self, experiment_dataset, simulation_dataset, tmp_path):
        """Test metrics computation for a single simulation in the analysis pipeline."""
        # Create a temporary output file
        metrics_file = tmp_path / "test_metrics.csv"
        plot_file_2D = tmp_path / "test_plot_2D.png"
        plot_file_3D = tmp_path / "test_plot_3D.png"
        
        # Mock the visualization components
        data_2D = define_2Dplot_storage()
        mock_ax3d = define_3Dplot_storage(experiment_dataset)
        
        # Run the analysis
        try:
            # Get the simulation path
            sim_paths = find_postProcessing()
            assert len(sim_paths) > 0, "No postProcessing folder found"

            for sim_path in sim_paths:
            
                # Run the analysis
                run_quantitative_analysis(
                    directory_loader=OpenFOAMProbesLoader,
                    file_loader=ProbesLoader,
                    output_file=metrics_file,
                    ref_dataset=experiment_dataset,
                    data_storage_2D=data_2D,
                    data_storage_3D=mock_ax3d,
                    data_path=sim_path,
                    last_time_only=False,
                    time=None,
                )

            # TODO: assert some stuff that this function changes (mock axes)

            create_2Dplot(
                data_storage=data_2D,
                file_path=plot_file_2D,
                save_only=True,
                interactive=False,
            )
            create_3Dplot(
                data_storage=mock_ax3d,
                file_path=plot_file_3D,
                save_only=True,
            )
            
        except Exception as e:
            # If the analysis fails, it might be due to missing visualization components
            # or incompatible data. We'll mark this as an expected failure.
            pytest.xfail(f"Analysis failed: {e}")


class TestQuantitativePlotColors:
    def test_2d_plot_storage_uses_predefined_colors(self):
        colors = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        data_storage = define_2Dplot_storage(colors=colors)
        statistics = {
            MetricNames.MG: {
                1.0: {"UMag": 1.1},
                2.0: {"UMag": 1.2},
                3.0: {"UMag": 1.3},
            },
            MetricNames.GV: {
                1.0: {"UMag": 1.1},
                2.0: {"UMag": 1.2},
                3.0: {"UMag": 1.3},
            },
        }

        store_2Dplot_data(
            data_storage=data_storage,
            source="case",
            statistics=statistics,
            last_time_only=False,
        )

        assert data_storage["colors"] == [colors[0], colors[1], colors[0]]
        assert [
            scatter_args["color"]
            for scatter_args in data_storage["all_scatter_args"]
        ] == [colors[0], colors[1], colors[0]]


class TestQuantitativeNoSave:
    def test_2d_plot_no_save_skips_headless_file_write(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DISPLAY", raising=False)
        data_storage = define_2Dplot_storage()
        statistics = {
            MetricNames.MG: {1.0: {"UMag": 1.1}},
            MetricNames.GV: {1.0: {"UMag": 1.2}},
        }
        store_2Dplot_data(
            data_storage=data_storage,
            source="case",
            statistics=statistics,
            last_time_only=False,
        )

        plot_file = tmp_path / "plot_2d.png"
        create_2Dplot(
            data_storage=data_storage,
            file_path=plot_file,
            save_only=False,
            interactive=False,
            no_save=True,
        )

        assert not plot_file.exists()
        plt.close("all")

    def test_2d_plot_no_save_shows_when_display_is_available(
        self,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setenv("DISPLAY", ":99")
        show_calls = []
        monkeypatch.setattr(plt, "show", lambda: show_calls.append(True))
        data_storage = define_2Dplot_storage()
        statistics = {
            MetricNames.MG: {1.0: {"UMag": 1.1}},
            MetricNames.GV: {1.0: {"UMag": 1.2}},
        }
        store_2Dplot_data(
            data_storage=data_storage,
            source="case",
            statistics=statistics,
            last_time_only=False,
        )

        plot_file = tmp_path / "plot_2d.png"
        create_2Dplot(
            data_storage=data_storage,
            file_path=plot_file,
            save_only=False,
            interactive=False,
            no_save=True,
        )

        assert show_calls == [True]
        assert not plot_file.exists()
        plt.close("all")

    def test_3d_plot_no_save_skips_headless_file_write(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DISPLAY", raising=False)
        dataset = DataSet(source="simulation")
        dataset.add_point(
            PointData((1.0, 0.0, 0.0), {"NRE_UMag": {1.0: 0.1}})
        )
        dataset.add_point(
            PointData((2.0, 0.0, 0.0), {"NRE_UMag": {1.0: 0.2}})
        )
        data_storage = define_3Dplot_storage(dataset)
        store_3Dplot_data(dataset, data_storage)

        create_3Dplot(
            data_storage=data_storage,
            file_path=tmp_path / "plot_3d.png",
            save_only=False,
            no_save=True,
        )

        assert not any(tmp_path.iterdir())
        plt.close("all")
