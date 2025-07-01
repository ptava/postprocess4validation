"""
Tests for the core module of the postprocess4validation package.

This module contains tests for the core functionality including:
- DataSet and PointData classes
- Data loading mechanisms
- Utility functions
"""
import pytest
from pathlib import Path
import sys

# Add the parent directory to sys.path to make the src module importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from postprocess4validation.core import (
    DataSet,
    PointData,
    CSVDataLoader,
    PointDataError,
    DataSetError,
)


class TestPointData:
    """Tests for the PointData class."""

    def test_point_data_creation(self):
        """Test creating a PointData object with valid coordinates."""
        coords = (1.0, 2.0, 3.0)
        point = PointData(coords, {})
        assert point.coordinates == coords
        assert point.fields == {}

    def test_point_data_field_access(self):
        """Test accessing fields in a PointData object."""
        coords = (1.0, 2.0, 3.0)
        fields = {"velocity": {0.0: 1.0, 1.0: 2.0}}
        point = PointData(coords, fields)
        
        # Test dictionary-style access
        assert point["velocity", 0.0] == 1.0
        assert point["velocity", 1.0] == 2.0
        
        # Test field existence check
        assert "velocity" in point.fields
        assert "pressure" not in point.fields

    def test_point_data_field_assignment(self):
        """Test assigning field values to a PointData object."""
        coords = (1.0, 2.0, 3.0)
        point = PointData(coords, {})
        
        # Assign a new field
        point["velocity"] = {0.0: 1.0, 1.0: 2.0}
        assert point["velocity", 0.0] == 1.0
        
        # Update an existing field
        point["velocity", 2.0] = 3.0
        assert point["velocity", 2.0] == 3.0


    def test_point_data_check_times_consistent(self):
        """Test time consistency check with consistent times."""
        coords = (1.0, 2.0, 3.0)
        fields = {
            "velocity": {0.0: 1.0, 1.0: 2.0},
            "pressure": {0.0: 10.0, 1.0: 20.0}
        }
        point = PointData(coords, fields)
        print(point)

        # Should not raise an exception
        point.get_times()

    def test_point_data_check_times_inconsistent(self):
        """Test time consistency check with inconsistent times."""
        coords = (1.0, 2.0, 3.0)
        fields = {
            "velocity": {0.0: 1.0, 1.0: 2.0},
            "pressure": {0.0: 10.0, 2.0: 20.0}  # Different time value
        }
        point = PointData(coords, fields)

        # Should raise an exception
        with pytest.raises(PointDataError):
            point.get_times()


class TestDataSet:
    """Tests for the DataSet class."""

    def test_dataset_creation(self):
        """Test creating a DataSet object."""
        dataset = DataSet(source="test")
        assert dataset.source == "test"
        assert len(dataset) == 0
        assert dataset.points == []
        assert dataset.fields == {}

    def test_dataset_add_point(self):
        """Test adding points to a DataSet."""
        dataset = DataSet(source="test")
        point1 = PointData((1.0, 2.0, 3.0), {"velocity": {0.0: 1.0}})
        point2 = PointData((4.0, 5.0, 6.0), {"velocity": {0.0: 2.0}})
        
        dataset.add_point(point1)
        dataset.add_point(point2)
        
        assert len(dataset) == 2
        assert dataset.points[0] == point1
        assert dataset.points[1] == point2

    def test_dataset_get_field_values(self):
        """Test getting field values from a DataSet."""
        field_test = "velocity"
        dataset = DataSet(source="test")
        point1 = PointData((1.0, 2.0, 3.0), {field_test: {0.0: 1.0, 1.0: 2.0}})
        point2 = PointData((4.0, 5.0, 6.0), {field_test: {0.0: 3.0, 1.0: 4.0}})

        dataset.add_point(point1)
        dataset.add_point(point2)

        assert field_test in dataset.fields

        values = dataset.get_field_values(field_test, 0.0)
        assert values == [1.0, 3.0]

        values = dataset.get_field_values(field_test, 1.0)
        assert values == [2.0, 4.0]

    def test_dataset_get_all_coordinates(self):
        """Test getting all coordinates from a DataSet."""
        dataset = DataSet(source="test")
        point1 = PointData((1.0, 2.0, 3.0), {})
        point2 = PointData((4.0, 5.0, 6.0), {})
        
        dataset.add_point(point1)
        dataset.add_point(point2)
        
        coords = dataset.get_all_coordinates()
        assert coords == [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]

    def test_dataset_check_times_consistent(self):
        """Test time consistency check with consistent times."""
        dataset = DataSet(source="test")
        point1 = PointData((1.0, 2.0, 3.0), {"velocity": {0.0: 1.0, 1.0: 2.0}})
        point2 = PointData((4.0, 5.0, 6.0), {"velocity": {0.0: 3.0, 1.0: 4.0}})

        dataset.add_point(point1)
        dataset.add_point(point2)

        # Should not raise an exception
        dataset.check_times()

    def test_dataset_check_times_inconsistent(self):
        """Test time consistency check with inconsistent times."""
        dataset = DataSet(source="test")
        point1 = PointData((1.0, 2.0, 3.0), {"velocity": {0.0: 1.0, 1.0: 2.0}})
        point2 = PointData((4.0, 5.0, 6.0), {"velocity": {0.0: 3.0, 2.0: 4.0}})  # Different time

        dataset.add_point(point1)
        dataset.add_point(point2)

        # Should raise an exception
        with pytest.raises(DataSetError):
            dataset.check_times()


class TestCSVDataLoader:
    """Tests for the CSVDataLoader class."""

    def test_csv_data_loader_load(self, experiment_data_path):
        """Test loading data with CSVDataLoader."""
        loader = CSVDataLoader(source="test")
        dataset = loader.load(experiment_data_path)
        
        assert isinstance(dataset, DataSet)
        assert dataset.source == "test"
        assert len(dataset) > 0
        
        # Check that points have been loaded
        assert len(dataset.points) > 0
        
        # Check that fields have been loaded
        assert len(dataset.fields) > 0
        
        # Check that each point has field data
        for point in dataset.points:
            assert len(point.fields) > 0


class TestDataLoading:
    """Integration tests for data loading functionality."""

    def test_experiment_dataset_fixture(self, experiment_dataset):
        """Test the experiment_dataset fixture."""
        assert isinstance(experiment_dataset, DataSet)
        assert experiment_dataset.source == "experiment"
        assert len(experiment_dataset) > 0
        
        # Check that points have coordinates
        for point in experiment_dataset.points:
            assert len(point.coordinates) == 3
            
        # Check that fields exist
        assert len(experiment_dataset.fields) > 0

    def test_simulation_dataset_fixture(self, simulation_dataset):
        """Test the simulation_dataset fixture."""
        assert isinstance(simulation_dataset, DataSet)
        assert len(simulation_dataset) > 0

        # Check that points have coordinates
        for point in simulation_dataset.points:
            assert len(point.coordinates) == 3

        # Check that fields exist
        assert len(simulation_dataset.fields) > 0

    def test_datasets_compatibility(self, experiment_dataset, simulation_dataset):
        """Test that experiment and simulation datasets are compatible."""
        # Check that both datasets have points
        assert len(experiment_dataset) > 0
        assert len(simulation_dataset) > 0

        # Check that both datasets have at least one common field
        exp_fields = set(experiment_dataset.fields.keys())
        sim_fields = set(simulation_dataset.fields.keys())
        assert len(exp_fields.intersection(sim_fields)) > 0

        # Check that time values are available
        exp_times = experiment_dataset.points[0].get_times()
        sim_times = simulation_dataset.points[0].get_times()
        assert len(exp_times) > 0
        assert len(sim_times) > 0
