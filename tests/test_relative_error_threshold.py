"""Pointwise relative-error threshold and 3D data tests."""

import sys

import numpy as np
import pytest
from matplotlib import pyplot as plt

from postprocess4validation.core import DataSet, PointData
from postprocess4validation.quantitative.computations import (
    _compute_relative_errors,
    compute_metrics,
)
from postprocess4validation.quantitative.parser import parser
from postprocess4validation.quantitative.visualization import (
    create_3Dplot,
    define_3Dplot_storage,
    store_3Dplot_data,
)


def _datasets(observed, predicted):
    experiment = DataSet(source="experiment")
    simulation = DataSet(source="simulation")
    for index, (observation, prediction) in enumerate(zip(observed, predicted)):
        coordinates = (float(index), 0.0, 0.0)
        experiment.add_point(PointData(coordinates, {"u": observation}))
        simulation.add_point(PointData(coordinates, {"u": prediction}))
    return experiment, simulation


def test_relative_errors_include_small_observations_and_large_errors():
    errors = _compute_relative_errors([1e-8, -2.0, 0.0, 0.0], [3e-8, 4.0, 1.0, 0.0])
    assert errors[:2].tolist() == pytest.approx([2.0, 3.0])
    assert np.isnan(errors[2:]).all()


def _storage(observed, predicted, **kwargs):
    experiment, simulation = _datasets(observed, predicted)
    compute_metrics(experiment, simulation)
    storage = define_3Dplot_storage(experiment)
    store_3Dplot_data(simulation, storage, reference_dataset=experiment, **kwargs)
    return storage, simulation


def test_default_cutoff_retains_boundary_and_raw_values():
    storage, simulation = _storage([1.0, 1.0, 0.0], [3.0, 4.0, 2.0])
    assert storage["fields_values"][0][:2].tolist() == pytest.approx([200.0, 300.0])
    assert storage["above_threshold"][0].tolist() == [False, True, False]
    assert storage["undefined"][0].tolist() == [False, False, True]
    assert storage["predictions"][0].tolist() == [3.0, 4.0, 2.0]
    assert storage["observations"][0].tolist() == [1.0, 1.0, 0.0]
    assert simulation.points[1]["NRE_u", 0.0] == pytest.approx(3.0)


def test_3d_storage_requires_reference_values_for_hover():
    _, simulation = _datasets([1.0], [2.0])
    simulation.fields["NRE_u"] = None
    with pytest.raises(ValueError, match="reference_dataset"):
        store_3Dplot_data(simulation, define_3Dplot_storage(simulation))


def test_cli_cutoff_controls_storage(monkeypatch):
    for argv, expected in [(["quantitative-cli"], [False, True]),
                           (["quantitative-cli", "--relative-error-threshold", "350"], [False, False])]:
        monkeypatch.setattr(sys, "argv", argv)
        args = parser()
        storage, _ = _storage([1.0, 1.0], [3.0, 4.0], relative_error_threshold=args.relative_error_threshold)
        assert storage["above_threshold"][0].tolist() == expected


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_cli_help_exits_successfully_with_percentage_cutoff(flag, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["quantitative-cli", flag])
    with pytest.raises(SystemExit) as exit_info:
        parser()
    assert exit_info.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "--relative-error-threshold" in help_text
    assert "200%" in help_text
    assert "red markers" in help_text


@pytest.mark.parametrize("cutoff", [0, -1, float("nan"), float("inf")])
def test_invalid_cutoff_is_rejected(cutoff, monkeypatch):
    with pytest.raises(ValueError, match="finite positive"):
        _storage([1.0], [2.0], relative_error_threshold=cutoff)
    monkeypatch.setattr(sys, "argv", ["quantitative-cli", "--relative-error-threshold", str(cutoff)])
    with pytest.raises(SystemExit):
        parser()


def test_plot_filters_scale_and_preserves_all_hover_pairs(tmp_path):
    storage, _ = _storage([1.0, 1.0, 0.0, -2.0], [3.0, 4.0, 2.0, -1.0])
    create_3Dplot(storage, tmp_path / "relative-error.png", save_only=True)
    figure = plt.gcf()
    axes = figure.axes[0]
    regular, above, undefined = axes.collections[:3]
    assert regular.cmap.name == "viridis"
    assert regular.get_clim() == pytest.approx((0.0, 200.0))
    assert len(regular.get_array()) == 2
    for artist in (above, undefined):
        assert artist.get_facecolors()[0, :3].tolist() == pytest.approx([1, 0, 0])
    assert [text.get_text() for text in axes.get_legend().get_texts()] == [
        "Relative error above threshold", "Relative error undefined"
    ]
    assert figure.axes[1].get_ylabel() == "Relative error for u [%] @ 0.0"
    assert "Predicted: 4" in above._p4v_hover_texts[0]
    assert "Observed: 1" in above._p4v_hover_texts[0]
    assert "Relative error: 300.000%" in above._p4v_hover_texts[0]
    assert "Predicted: 2" in undefined._p4v_hover_texts[0]
    assert "Observed: 0" in undefined._p4v_hover_texts[0]
    assert "Relative error undefined" in undefined._p4v_hover_texts[0]
    assert "Predicted: -1" in regular._p4v_hover_texts[1]
    assert "Observed: -2" in regular._p4v_hover_texts[1]
    plt.close(figure)


@pytest.mark.parametrize("observed,predicted,legend", [
    ([1.0, 2.0], [2.0, 3.0], None),
    ([1.0, 1.0], [4.0, 5.0], "Relative error above threshold"),
    ([0.0, 0.0], [1.0, 0.0], "Relative error undefined"),
])
def test_plot_handles_no_exclusions_and_all_excluded(tmp_path, observed, predicted, legend):
    storage, _ = _storage(observed, predicted)
    create_3Dplot(storage, tmp_path / "relative-error.png", save_only=True)
    figure = plt.gcf()
    axes = figure.axes[0]
    if legend is None:
        assert axes.get_legend() is None
        assert len(figure.axes) == 2
    else:
        assert [text.get_text() for text in axes.get_legend().get_texts()] == [legend]
        assert len(figure.axes) == 1
    plt.close(figure)
