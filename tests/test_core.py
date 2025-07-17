"""
Tests for the core module of the postprocess4validation package.

This module contains tests for the core functionality including:
- DataSet and PointData classes
- Data loading mechanisms
- Utility functions
"""
import sys
from pathlib import Path
import pytest
from argparse import ArgumentTypeError

# Add the parent directory to sys.path to make the src module importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from postprocess4validation.core import (
    validate_path,
    file_path,
    dir_path,
    output_path,
    get_time_subfolders,
    get_latest_time_subfolder,
    PlaneSet,
    DataSet,
    PointData,
    CSVDataLoader,
    PointDataError,
    DataSetError,
    NoTimeFolderError,
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

    def test_dataset_add_field_value_get_point(self):
        """Test adding a field value and retrieving points."""
        dataset = DataSet(source="test")
        coords = (1.0, 2.0, 3.0)
        point = PointData(coords, {"velocity": {0.0: 1.0}})
        dataset.add_point(point)
        dataset.add_field_value("velocity", 1.0, 2.0, coords)

        retrieved_point = dataset.get_point_by_coordinates(coords)
        assert isinstance(retrieved_point, PointData)
        assert retrieved_point.coordinates == coords
        assert retrieved_point["velocity", 0.0] == 1.0
        assert retrieved_point["velocity", 1.0] == 2.0

    def test_dataset_get_all_times_and_points_to_planes(self, experiment_data_path):
        """Ensure planes and lines are generated correctly from sample data."""
        loader = CSVDataLoader(source="experiment")
        dataset = loader.load(experiment_data_path)

        times = dataset.get_all_times()
        assert times == [0.0]

        planes = dataset.points_to_planes(flow_direction='X')
        assert isinstance(planes, PlaneSet)

        unique_z = {p.z for p in dataset.points}
        unique_y = {p.y for p in dataset.points}
        assert len(planes) == len(unique_z) + len(unique_y)

        for z in unique_z:
            plane = planes.get_plane("XY", z)
            assert plane is not None
            expected = {p.x for p in dataset.points if p.z == z}
            assert len(plane.lines) == len(expected)

        for y in unique_y:
            plane = planes.get_plane("XZ", y)
            assert plane is not None
            expected = {p.x for p in dataset.points if p.y == y}
            assert len(plane.lines) == len(expected)



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


class TestValidatePath:
    def test_validate_path_success(self, tmp_path):
        print('DEBUG',tmp_path)
        file = tmp_path / "file.txt"
        file.write_text("content")
        directory = tmp_path / "subdir"
        directory.mkdir()

        assert validate_path(file, must_exist=True, must_be_file=True) == file
        assert validate_path(directory, must_exist=True, must_be_dir=True) == directory
        # passing as string should also work
        assert validate_path(str(file)) == file

    def test_validate_path_failures(self, tmp_path):
        file = tmp_path / "file.txt"
        file.write_text("content")

        with pytest.raises(ValueError):
            validate_path(tmp_path / "missing.txt")

        with pytest.raises(ValueError):
            validate_path(file, must_be_dir=True)

        with pytest.raises(ValueError):
            validate_path(tmp_path, must_be_file=True)

        # When must_exist is False the path is returned regardless of existence
        new_file = tmp_path / "new.txt"
        assert validate_path(new_file, must_exist=False) == new_file


class TestWrapperPaths:
    def test_file_path_and_dir_path(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("x")
        d = tmp_path / "folder"
        d.mkdir()

        assert file_path(f) == f
        assert dir_path(d) == d

        with pytest.raises(ArgumentTypeError):
            file_path(tmp_path / "missing.txt")
        with pytest.raises(ArgumentTypeError):
            file_path(d)

        with pytest.raises(ArgumentTypeError):
            dir_path(tmp_path / "missing")
        with pytest.raises(ArgumentTypeError):
            dir_path(f)

    def test_output_path(self, tmp_path):
        out = tmp_path / "result.csv"
        assert output_path(str(out)) == out

        with pytest.raises(ArgumentTypeError):
            output_path("")

        with pytest.raises(ArgumentTypeError):
            output_path(str(tmp_path / "missing_dir" / "out.csv"))


class TestOpenFOAMUtils:
    def test_time_subfolders_and_latest(self, tmp_path):
        pp_dir = tmp_path / "postProcessing" / "probes"
        pp_dir.mkdir(parents=True)
        for name in ["0", "0.5", "1"]:
            (pp_dir / name).mkdir()
        (pp_dir / "notes").mkdir()

        folders = get_time_subfolders(pp_dir)
        assert set(folders) == {"0", "0.5", "1"}
        assert get_latest_time_subfolder(pp_dir) == "1"

    def test_time_subfolders_no_valid(self, tmp_path):
        empty = tmp_path / "postProcessing" / "probes"
        empty.mkdir(parents=True)
        (empty / "abc").mkdir()

        with pytest.raises(NoTimeFolderError):
            get_time_subfolders(empty)
        with pytest.raises(NoTimeFolderError):
            get_latest_time_subfolder(empty)
