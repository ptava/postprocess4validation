"""
Tests for the qualitative module of the postProcess4Validation package.
"""
import pytest
from numpy import ndarray

from postprocess4validation.core import Line, Plane, PlaneSet, OpenFOAMError
from postprocess4validation.qualitative import (
    LinesDataLoader,
    OpenFOAMLinesLoader,
)

class TestQualitativeAnalysis:
    """Tests for qualitative analysis pipeline."""
    
    def test_extract_name_and_fields(self, line_file_path):
        name, fields = LinesDataLoader._extract_name_and_fields(line_file_path)
        assert name == "line_-0.02_0"
        assert fields == ["UMag", "k"]

    def test_load(self, line_file_path):
        loader = LinesDataLoader(source='test')
        name, data = loader.load(line_file_path)
        assert name == "line_-0.02_0"
        assert data.keys() == {"UMag", "k"}
        for field_dict in data.values():
            assert isinstance(field_dict, dict)
            assert loader.source in field_dict
            arr = field_dict[loader.source]
            assert isinstance(arr, ndarray)
            assert arr.shape[1] == 2

    def test_get_dirs(self):
        print('banana')

    def test_run_and_plot(self):
        print('banana')


class TestQualitativeTimeFiltering:
    """Tests for start-time filtering in qualitative data loading."""

    @staticmethod
    def _make_lines_case(tmp_path):
        post_processing = tmp_path / "postProcessing"
        lines_folder = post_processing / "lines"
        for time in ("0", "10"):
            time_folder = lines_folder / time
            time_folder.mkdir(parents=True)
            (time_folder / "line_-0.02_0_UMag_k.xy").write_text(
                "0.0 1.0 0.1\n1.0 2.0 0.2\n",
                encoding="utf-8",
            )

        plane = Plane("XY", 0.0)
        line = Line(tag="XY", plane_position=0.0, line_position=-0.02)
        plane.add_line(line)
        return post_processing, line

    def test_openfoam_lines_loader_filters_time_folders(self, tmp_path):
        post_processing, line = self._make_lines_case(tmp_path)
        loader = OpenFOAMLinesLoader(
            file_loader=LinesDataLoader,
            folder=post_processing,
            source="case",
            plane_set=PlaneSet([Plane("XY", 0.0)]),
            subfolder="lines",
            start_time=10.0,
        )
        loader.plane_set.get_plane("XY", 0.0).add_line(line)

        loader.load(post_processing)

        assert line.get_times("case", "UMag") == ["10"]

    def test_openfoam_lines_loader_raises_when_filter_removes_all_folders(
        self,
        tmp_path,
    ):
        post_processing, line = self._make_lines_case(tmp_path)
        plane = Plane("XY", 0.0)
        plane.add_line(line)
        plane_set = PlaneSet([plane])
        loader = OpenFOAMLinesLoader(
            file_loader=LinesDataLoader,
            folder=post_processing,
            source="case",
            plane_set=plane_set,
            subfolder="lines",
            start_time=11.0,
        )

        with pytest.raises(OpenFOAMError, match="time filters"):
            loader.load(post_processing)

