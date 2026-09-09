"""
Tests for the qualitative module of the postProcess4Validation package.
"""
from argparse import Namespace
from pathlib import Path

import pytest
from matplotlib import pyplot as plt
from numpy import array, ndarray

from postprocess4validation.core import Line, Plane, PlaneSet, OpenFOAMError
from postprocess4validation.qualitative import cli as qualitative_cli
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

    def test_cli_passes_custom_figure_size_to_create_plots(
        self,
        tmp_path,
        monkeypatch,
    ):
        captured_kwargs = {}

        class FakeExperimentLoader:
            def __init__(self, source):
                self.source = source

            def load(self, path):
                return self

            def points_to_planes(self):
                return PlaneSet([Plane("XY", 0.0)])

        args = Namespace(
            verbose=False,
            debug=False,
            loader_exp=FakeExperimentLoader,
            exp_data=Path("expData.csv"),
            fields=None,
            output_dir=tmp_path,
            single=Path("postProcessing"),
            exclude=None,
            include=None,
            loader_sim=(OpenFOAMLinesLoader, LinesDataLoader),
            start_time=None,
            save_only=True,
            no_save=False,
            interactive=False,
            stl=None,
            min_lines=1,
            scale=0.005,
            line_style="scatter",
            colors=None,
            xlim=None,
            ylim=None,
            zlim=None,
            figure_hsize=22.0,
            figure_vsize=9.0,
        )
        monkeypatch.setattr(qualitative_cli, "parser", lambda: args)
        monkeypatch.setattr(
            qualitative_cli,
            "run_qualitative_analysis",
            lambda *args, **kwargs: None,
        )

        def capture_create_plots(**kwargs):
            captured_kwargs.update(kwargs)

        monkeypatch.setattr(
            qualitative_cli,
            "create_plots",
            capture_create_plots,
        )

        assert qualitative_cli.main() == 0
        assert captured_kwargs["plot_hsize"] == 22.0
        assert captured_kwargs["plot_vsize"] == 9.0


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


class TestQualitativeLineStyle:
    """Tests for qualitative simulation line rendering styles."""

    @staticmethod
    def _line_with_data():
        line = Line(tag="XY", plane_position=0.0, line_position=-0.02)
        line.add_data(
            source="case",
            field="UMag",
            time=10.0,
            arr=array([[0.0, 1.0], [1.0, 2.0]]),
        )
        return line

    def test_line_add_to_plot_uses_scatter_by_default(self):
        line = self._line_with_data()
        fig, ax = plt.subplots()

        line.add_to_plot(ax=ax, field_name="UMag", last_time_only=False)

        assert len(ax.collections) == 1
        assert len(ax.lines) == 1
        plt.close(fig)

    def test_line_add_to_plot_can_use_continuous_lines(self):
        line = self._line_with_data()
        fig, ax = plt.subplots()

        line.add_to_plot(
            ax=ax,
            field_name="UMag",
            last_time_only=False,
            line_style="line",
        )

        assert len(ax.collections) == 0
        assert len(ax.lines) == 2
        plt.close(fig)

    def test_line_add_to_plot_uses_predefined_colors(self):
        line = self._line_with_data()
        colors = [(1.0, 0.0, 0.0)]
        fig, ax = plt.subplots()

        line.add_to_plot(
            ax=ax,
            field_name="UMag",
            last_time_only=False,
            colors=colors,
        )

        assert line.colors == colors
        assert ax.collections[0].get_facecolors()[0][:3].tolist() == list(colors[0])
        plt.close(fig)

    def test_line_add_to_plot_skips_missing_field(self):
        line = self._line_with_data()
        fig, ax = plt.subplots()

        plotted = line.add_to_plot(
            ax=ax,
            field_name="kMean",
            last_time_only=False,
        )

        assert plotted is False
        assert len(ax.collections) == 0
        assert len(ax.lines) == 0
        assert line.colors == []
        assert line.labels == []
        plt.close(fig)

    def test_line_add_to_plot_skips_missing_field_for_one_source(self):
        line = self._line_with_data()
        line.add_data(
            source="RANS",
            field="kMean",
            time=10.0,
            arr=array([[0.0, 0.1], [1.0, 0.2]]),
        )
        fig, ax = plt.subplots()

        plotted = line.add_to_plot(
            ax=ax,
            field_name="kMean",
            last_time_only=False,
        )

        assert plotted is True
        assert len(ax.collections) == 1
        assert len(ax.lines) == 1
        assert line.labels == ["10.0"]
        plt.close(fig)

    def test_plane_legend_keeps_labels_when_colors_cycle(self):
        line = self._line_with_data()
        line.add_data(
            source="case",
            field="UMag",
            time=20.0,
            arr=array([[0.0, 1.5], [1.0, 2.5]]),
        )
        plane = Plane("XY", 0.0)
        plane.add_line(line)
        fig, ax = plt.subplots()

        plane.add_to_plot(
            ax=ax,
            field_name="UMag",
            last_timestep_only=False,
            scale=1.0,
            colors=[(1.0, 0.0, 0.0)],
        )

        labels = [text.get_text() for text in ax.get_legend().texts]
        assert labels == ["10.0", "20.0"]
        plt.close(fig)

    def test_plane_add_to_plot_skips_missing_field_line(self):
        line = self._line_with_data()
        plane = Plane("XY", 0.0)
        plane.add_line(line)
        fig, ax = plt.subplots()

        plane.add_to_plot(
            ax=ax,
            field_name="kMean",
            last_timestep_only=False,
            scale=1.0,
        )

        assert len(ax.collections) == 0
        assert len(ax.lines) == 0
        plt.close(fig)
