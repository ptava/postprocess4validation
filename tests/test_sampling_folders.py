"""Tests for user-selectable OpenFOAM sampling folder names."""

import sys

import pytest

from postprocess4validation.core import DataSet, Line, Plane, PlaneSet, PointData
from postprocess4validation.qualitative.analysis import load_data_into_planeset
from postprocess4validation.qualitative.lines_data_loader import (
    LinesDataLoader,
    OpenFOAMLinesLoader,
)
from postprocess4validation.qualitative.parser import parser as qualitative_parser
from postprocess4validation.quantitative.analysis import run_quantitative_analysis
from postprocess4validation.quantitative.parser import parser as quantitative_parser
from postprocess4validation.quantitative.probes_data_loader import (
    OpenFOAMProbesLoader,
    ProbesLoader,
)
from postprocess4validation.quantitative.visualization import (
    define_2Dplot_storage,
    define_3Dplot_storage,
)


@pytest.mark.parametrize(
    ("parser", "option", "attribute", "default", "custom"),
    [
        (
            quantitative_parser,
            "--probes-folder",
            "probes_folder",
            "probes",
            "wakeProbes",
        ),
        (qualitative_parser, "--lines-folder", "lines_folder", "lines", "wakeLines"),
    ],
)
def test_sampling_folder_arguments_have_defaults_and_accept_custom_values(
    monkeypatch,
    parser,
    option,
    attribute,
    default,
    custom,
):
    monkeypatch.setattr(sys, "argv", ["postprocess4validation"])
    assert getattr(parser(), attribute) == default

    monkeypatch.setattr(sys, "argv", ["postprocess4validation", option, custom])
    assert getattr(parser(), attribute) == custom


def test_quantitative_analysis_loads_custom_probes_folder(tmp_path):
    post_processing = tmp_path / "case" / "postProcessing"
    probes = post_processing / "wakeProbes" / "0"
    probes.mkdir(parents=True)
    (probes / "u").write_text(
        "# Probe 0 (0 0 0)\n1 1.1\n",
        encoding="utf-8",
    )
    reference = DataSet(
        source="experiment",
        points=[PointData((0.0, 0.0, 0.0), {"u": {0.0: 1.0}})],
    )

    results = run_quantitative_analysis(
        directory_loader=OpenFOAMProbesLoader,
        file_loader=ProbesLoader,
        output_file=tmp_path / "statistics.csv",
        ref_dataset=reference,
        data_storage_2D=define_2Dplot_storage(),
        data_storage_3D=define_3Dplot_storage(reference),
        data_path=post_processing,
        probes_folder="wakeProbes",
        write_output=False,
    )

    assert results["RMSE"][1.0]["u"] == pytest.approx(0.1)


def test_qualitative_analysis_loads_custom_lines_folder(tmp_path):
    post_processing = tmp_path / "case" / "postProcessing"
    lines = post_processing / "wakeLines" / "0"
    lines.mkdir(parents=True)
    (lines / "line_-0.02_0_UMag.xy").write_text(
        "0.0 1.0\n1.0 2.0\n",
        encoding="utf-8",
    )
    plane = Plane("XY", 0.0)
    line = Line(tag="XY", plane_position=0.0, line_position=-0.02)
    plane.add_line(line)

    load_data_into_planeset(
        plane_set=PlaneSet([plane]),
        directory_loader=OpenFOAMLinesLoader,
        file_loader=LinesDataLoader,
        data_path=post_processing,
        lines_folder="wakeLines",
    )

    assert line.get_times("case", "UMag") == ["0"]
