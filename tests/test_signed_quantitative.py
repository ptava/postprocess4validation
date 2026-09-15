"""Signed scalar comparisons must retain usable statistics and error plots."""
import csv
import sys

import numpy as np
import pytest
from matplotlib import pyplot as plt

from postprocess4validation.core import CSVDataLoader, DataSet, PointData, write_metrics
from postprocess4validation.quantitative import computations
from postprocess4validation.quantitative.cli import main
from postprocess4validation.quantitative.analysis import run_datasets_comparison
from postprocess4validation.quantitative.visualization import (
    define_2Dplot_storage, define_3Dplot_storage, store_2Dplot_data, store_3Dplot_data,
)


def datasets(observed, predicted):
    experiment = DataSet(source="experiment")
    simulation = DataSet(source="simulation")
    for i, (obs, pred) in enumerate(zip(observed, predicted)):
        experiment.add_point(PointData((float(i), 0.0, 0.0), {"u": obs}))
        simulation.add_point(PointData((float(i), 0.0, 0.0), {"u": pred}))
    return experiment, simulation


@pytest.mark.parametrize("observed,predicted,expected", [
    ([1, 2], [2, 4], np.sqrt(2.5)),
    ([-1, -2], [-2, -4], np.sqrt(2.5)),
    ([-1, 1], [-1, 1], 0),
    ([0, 0], [0, 0], 0),
    ([1, 2], [-1, -2], np.sqrt(10)),
])
def test_rmse(observed, predicted, expected):
    assert computations._compute_rmse(predicted, observed) == pytest.approx(expected)


@pytest.mark.parametrize("observed,predicted", [
    ([1, 2], [1]), ([], []), ([np.nan], [1]), ([1], [np.inf]),
])
def test_rmse_rejects_invalid_pairs(observed, predicted):
    with pytest.raises(ValueError):
        computations._compute_rmse(predicted, observed)


@pytest.mark.parametrize("observed,predicted", [
    ([-1, -2], [-1, -3]), ([1, 2], [-1, -2]),
    ([-1, 1], [-1, 1]), ([-1, 1], [1, 1]),
])
def test_negative_comparisons_only_have_rmse_and_relative_errors(observed, predicted):
    experiment, simulation = datasets(observed, predicted)
    results = computations.compute_metrics(experiment, simulation)
    assert set(results) == {"RMSE"}
    assert results["RMSE"][0.0]["u"] == pytest.approx(
        np.sqrt(np.mean((np.array(observed) - predicted) ** 2))
    )
    for i, (obs, pred) in enumerate(zip(observed, predicted)):
        assert simulation.points[i]["NRE_u", 0.0] == pytest.approx(abs(obs - pred) / abs(obs))


def test_positive_comparisons_keep_existing_metrics():
    experiment, simulation = datasets([1, 2], [2, 4])
    assert set(computations.compute_metrics(experiment, simulation)) == {
        "RMSE", "NMSE", "MG", "GV",
    }


def test_latest_negative_sample_does_not_plot_older_geometric_metrics(tmp_path):
    experiment, simulation = datasets([1, 2], [{0: 1, 1: -1}, {0: 2, 1: -2}])
    results = computations.compute_metrics(experiment, simulation)
    storage = define_2Dplot_storage()
    store_2Dplot_data(storage, "simulation", results, last_time_only=True)
    assert storage["all_scatter_args"] == []
    path = tmp_path / "statistics.csv"
    write_metrics(path, "simulation", results, True, 6)
    with path.open() as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ["Id", "RMSE-u"]
    assert rows[1] == ["simulation", str(round(np.sqrt(10), 6))]


def test_csv_comparison_retains_signed_relative_error_plot_data(tmp_path):
    experiment, _ = datasets([-1, 1], [-1, 1])
    path = tmp_path / "comparison.csv"
    path.write_text("x,y,z,u(m/s)\n0,0,0,-2\n1,0,0,1\n")
    storage_2d = define_2Dplot_storage()
    storage_3d = define_3Dplot_storage(experiment)
    results = run_datasets_comparison(
        CSVDataLoader, tmp_path / "statistics.csv", experiment,
        storage_2d, storage_3d, [path],
    )
    assert set(results["comparison"]) == {"RMSE"}
    assert storage_2d["all_scatter_args"] == []
    assert storage_3d["fields_values"][0].tolist() == [1, 0]
    assert "RMSE-u" in (tmp_path / "statistics.csv").read_text()


def test_csv_repeats_header_when_returning_to_an_earlier_metric_set(tmp_path):
    path = tmp_path / "statistics.csv"
    signed = {"RMSE": {0: {"u": 1}}}
    positive = {"RMSE": {0: {"u": 1}}, "NMSE": {0: {"u": 0.5}}}
    for source, results in [("signed1", signed), ("positive", positive), ("signed2", signed)]:
        write_metrics(path, source, results, True)
    with path.open() as stream:
        rows = list(csv.reader(stream))
    assert rows == [
        ["Id", "RMSE-u"], ["signed1", "1"],
        ["Id", "RMSE-u", "NMSE-u"], ["positive", "1", "0.5"],
        ["Id", "RMSE-u"], ["signed2", "1"],
    ]


def test_zero_reference_is_excluded_only_from_relative_error(caplog):
    experiment, simulation = datasets([-1, 0, 1], [-2, 3, 1])
    results = computations.compute_metrics(experiment, simulation)
    assert results["RMSE"][0.0]["u"] == pytest.approx(np.sqrt(10 / 3))
    storage = define_3Dplot_storage(simulation)
    store_3Dplot_data(simulation, storage)
    assert storage["coordinates"][0].tolist() == [[0, 0, 0], [2, 0, 0]]
    assert storage["fields_values"][0].tolist() == [1, 0]
    assert "zero" in caplog.text.lower()


def test_mixed_fields_and_times_write_aligned_csv(tmp_path):
    experiment, simulation = datasets([1, 2], [{0: 1, 1: -1}, {0: 2, 1: -2}])
    for dataset in (experiment, simulation):
        for point in dataset.points:
            point["k", 0.0] = 2.0
            if dataset is simulation:
                point["k", 1.0] = 2.0
        dataset.fields["k"] = None
    results = computations.compute_metrics(experiment, simulation)
    assert results["RMSE"][1]["u"] == pytest.approx(np.sqrt(10))
    for metric in ("NMSE", "MG", "GV"):
        assert "u" in results[metric][0]
        assert "u" not in results[metric][1]
        assert "k" in results[metric][1]
    path = tmp_path / "statistics.csv"
    write_metrics(path, "simulation", results, False, 6)
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    assert all(None not in row for row in rows)
    assert float(rows[1]["RMSE-u"]) == pytest.approx(np.sqrt(10), abs=1e-6)
    assert rows[1]["NMSE-u"] == ""
    assert float(rows[1]["MG-k"]) == 1


@pytest.mark.parametrize("observed,predicted,has_plot", [
    ([-1, 1], [-2, 1], True),
    ([-1, 0, 1], [-2, 3, 1], True),
    ([0, 0], [-1, 1], False),
])
def test_signed_cli_writes_rmse_and_available_error_plot(
    tmp_path, monkeypatch, observed, predicted, has_plot,
):
    probes = tmp_path / "case" / "postProcessing" / "probes" / "0"
    probes.mkdir(parents=True)
    header = "".join(f"# Probe {i} ({i} 0 0)\n" for i in range(len(observed)))
    (probes / "u").write_text(header + "1 " + " ".join(map(str, predicted)) + "\n")
    experiment = tmp_path / "experiment.csv"
    experiment.write_text("x,y,z,u(m/s)\n" + "".join(
        f"{i},0,0,{value}\n" for i, value in enumerate(observed)
    ))
    monkeypatch.setattr(sys, "argv", [
        "quantitative-cli", "--single", str(probes.parent.parent),
        "--exp-data", str(experiment), "--output-dir", str(tmp_path), "--save-only",
    ])
    try:
        assert main() == 0
        statistics = (tmp_path / "statistics.csv").read_text()
        assert "RMSE-u" in statistics
        assert all(metric not in statistics for metric in ("NMSE", "MG", "GV"))
        assert not (tmp_path / "2d_plot.png").exists()
        plots = list(tmp_path.glob("3d_plot*.png"))
        assert bool(plots) == has_plot
        if has_plot:
            assert plots[0].stat().st_size > 1000
    finally:
        plt.close("all")
