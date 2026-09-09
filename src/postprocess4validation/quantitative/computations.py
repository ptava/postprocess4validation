from math import exp
from numpy import (
    mean as npmean,
    ndarray, 
    log as nplog, 
    any,
    abs as npabs,
)
from typing import Any, Dict, List, Optional, Tuple, Union, KeysView

from ..core import DataSet, PointData
from .utils import (
    logger,
    safe_array_conversion,
    MetricNames,
    ValidationConstants,
)


def store_individual_contribution(
    dataset: DataSet,
    name: str,
    time: float,
    contributions: ndarray,
    point_coordinates: Optional[List[Tuple[float, float, float]]] = None,
) -> None:
    """
    Store individual contributions into the dataset for a specific field and time.
    Update the dataset fields dictionary
    
    Parameters
    ----------
    dataset (DataSet): the dataset to which contributions will be assigned.
    field (str): the field name for which contributions are being assigned.
    time (float): the time step at which contributions are being assigned.
    contributions (ndarray): array of contributions to assign.
    """
    if point_coordinates is None:
        points : List[PointData] = dataset.points

        if len(points) != len(contributions):
            raise ValueError(
                f"Size mismatch: points has {len(points)} elements, "
                f"contributions has {len(contributions)} elements"
            )
        for idx, point in enumerate(points):
            point[name, time] = contributions[idx]
    else:
        if len(point_coordinates) != len(contributions):
            raise ValueError(
                f"Size mismatch: coordinates has {len(point_coordinates)} "
                f"elements, contributions has {len(contributions)} elements"
            )
        for idx, coordinates in enumerate(point_coordinates):
            point = dataset.get_point_by_coordinates(coordinates)
            if point is None:
                logger.warning(
                    f"Skipping contribution for missing point {coordinates} in "
                    f"{dataset.source} dataset."
                )
                continue
            point[name, time] = contributions[idx]

    # Store new field name and units
    dataset.fields[name] = None


def _matching_coordinates(
    dataset_from_exp: DataSet,
    dataset_from_sim: DataSet,
) -> List[Tuple[float, float, float]]:
    exp_coordinates = set(dataset_from_exp.get_all_coordinates())
    sim_coordinates = dataset_from_sim.get_all_coordinates()
    sim_coordinates_set = set(sim_coordinates)

    missing_in_exp = [
        coordinates
        for coordinates in sim_coordinates
        if coordinates not in exp_coordinates
    ]
    missing_in_sim = [
        coordinates
        for coordinates in exp_coordinates
        if coordinates not in sim_coordinates_set
    ]

    if missing_in_exp:
        logger.warning(
            f"Skipping {len(missing_in_exp)} simulation probe point(s) without "
            "matching experiment coordinates."
        )
    if missing_in_sim:
        logger.warning(
            f"Skipping {len(missing_in_sim)} experiment point(s) without "
            "matching simulation probe coordinates."
        )

    matching = [
        coordinates
        for coordinates in sim_coordinates
        if coordinates in exp_coordinates
    ]
    if not matching:
        raise ValueError(
            "No matching point coordinates found between experiment and "
            "simulation datasets."
        )
    return matching


def _aligned_field_values(
    dataset_from_exp: DataSet,
    dataset_from_sim: DataSet,
    field_name: str,
    time: float,
    coordinates: List[Tuple[float, float, float]],
) -> Tuple[List[Tuple[float, float, float]], List[Any], List[Any]]:
    matched_coordinates = []
    experiment_values = []
    prediction_values = []

    for coordinate in coordinates:
        exp_point = dataset_from_exp.get_point_by_coordinates(coordinate)
        sim_point = dataset_from_sim.get_point_by_coordinates(coordinate)
        if exp_point is None or sim_point is None:
            logger.warning(
                f"Skipping coordinate {coordinate} for field {field_name}: "
                "point missing in one dataset."
            )
            continue
        try:
            experiment_value = exp_point[field_name, 0]
        except (KeyError, TypeError):
            logger.warning(
                f"Skipping coordinate {coordinate}: experiment field "
                f"{field_name!r} is missing at time 0."
            )
            continue
        try:
            prediction_value = sim_point[field_name, time]
        except (KeyError, TypeError):
            logger.warning(
                f"Skipping coordinate {coordinate}: simulation field "
                f"{field_name!r} is missing at time {time}."
            )
            continue

        matched_coordinates.append(coordinate)
        experiment_values.append(experiment_value)
        prediction_values.append(prediction_value)

    return matched_coordinates, experiment_values, prediction_values


def compute_metrics(
    dataset_from_exp: DataSet,
    dataset_from_sim: DataSet,
    time_values: Optional[KeysView[float]] = None,
    fields: Optional[List[str]] = None
) -> Dict[str, Dict[float, Dict[str, float]]]:
    """
    Compute statistical metrics for comparing experiment and simulation 
    datasets.
    
    This function computes several metrics (NMSE, MG, GV) for each field at each time.
    The results are stored in a nested dictionary of the form:
        {
            "NMSE": {time1: {field1: val, field2: val, ...}, time2: {...}, ...},
            "MG":   {time1: {...}, time2: {...}, ...},
            "GV":   {time1: {...}, time2: {...}, ...},
        }

    Each metric function stores individual point contributions in the dataset.
    
    Parameters
    ----------
    dataset_from_exp (DataSet): dataset containing the experiment data.
    dataset_from_sim (DataSet): dataset containing the simulation data.
    time_values : list(optional):  list of time steps. If not provided, 
        attempts to retrieve from simulation dataset.
    fields : list(optional): list of field names. If not provided, uses fields
        from the first point in the simulation dataset.
        
    Returns
    -------
    dict: Nested dictionary containing computed metrics for each field at each time.
        
    Raises
    ------
    ValueError: if datasets are empty or incompatible
    TypeError: if inputs are not of the expected types
    """
    # Check if datasets are empty
    if len(dataset_from_exp) == 0:
        raise ValueError("Experiment dataset is empty")
    if len(dataset_from_sim) == 0:
        raise ValueError("Simulation dataset is empty")
    
    # Available metrics
    metrics = {
        MetricNames.NMSE: _compute_nmse,
        MetricNames.MG:   _compute_mean_bias,
        MetricNames.GV:   _compute_geometric_variance
    }

    # Get reference point for fields and times if not provided
    try:
        ref_point = dataset_from_sim[0]
    except IndexError:
        raise ValueError("Simulation dataset has no points")
    
    # Extract fields if not provided
    exp_fields = set(dataset_from_exp.fields.keys())
    sim_fields = set(dataset_from_sim.fields.keys())

    if fields is None:
        common_fields = exp_fields.intersection(sim_fields)
    else:
        common_fields = set(fields).intersection(exp_fields, sim_fields)
        unavailable_fields = set(fields) - common_fields
        if unavailable_fields:
            raise ValueError(
                "Requested field(s) are not available in both experiment and "
                f"simulation datasets: {sorted(unavailable_fields)}"
            )

    if not common_fields:
        raise ValueError("No common fields found between experiment and "
                         "simulation datasets")
    
    # Extract time values if not provided
    if time_values is None:
        time_values = ref_point.get_times()
        if not time_values:
            raise ValueError("No time values found in the simulation dataset")

    # Check if at least one dataset source is 'experiment'
    if dataset_from_exp.source.lower() != "experiment" \
        and dataset_from_sim.source.lower() != "experiment":
        raise ValueError("At least one dataset must have 'experiment' as its source.")

    # Get dataset points coordinates that are available in both datasets.
    points_coordinates = _matching_coordinates(dataset_from_exp, dataset_from_sim)
    if not points_coordinates:
        raise ValueError("No matching coordinates found between datasets")

    # Initialize results dictionary
    results = {}
    
    # Process each field and time
    for f in common_fields:
        for t in time_values:
            try:
                (
                    matched_coordinates,
                    experiment,
                    predictions,
                ) = _aligned_field_values(
                    dataset_from_exp=dataset_from_exp,
                    dataset_from_sim=dataset_from_sim,
                    field_name=f,
                    time=t,
                    coordinates=points_coordinates,
                )
                
                if len(predictions) == 0 or len(experiment) == 0:
                    logger.warning(
                        f"Skipping time {t} for field {f} due to missing "
                        "matched experiment/simulation data"
                    )
                    continue
                
                # Store relative error contributions
                relative_errrors = _compute_relative_errors(experiment, predictions)
                store_individual_contribution(
                    dataset_from_sim, 
                    f"{MetricNames.NRE}_{f}", 
                    t, 
                    relative_errrors,
                    point_coordinates=matched_coordinates,
                )

                # Compute statistical metrics
                for metric_name, metric_func in metrics.items():
                    try:
                        value = metric_func(
                            predictions,
                            experiment
                        )
                        # Nesting structure: results[metric_name][t][field] = value
                        results.setdefault(
                            metric_name, {}
                        ).setdefault(t, {})[f] = value
                        logger.debug(
                            f"Computed {metric_name} for field {f} at time {t}:"
                            f" {value}")
                    except (ValueError, TypeError) as e:
                        # Log the error but continue with other metrics
                        logger.warning(
                            f"Could not compute {metric_name} for field {f} at "
                            f"time {t}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Error processing field {f} at time {t}: {e}")
                continue

    if not results:
        raise ValueError("No valid metrics could be computed. Check your "
                         "datasets for compatibility.")
        
    return results

def _compute_relative_errors(
    experiment: Union[List, ndarray],
    predictions: Union[List, ndarray]
) -> ndarray:
    """
    Compute relative error contributions for each point.
    
    Parameters
    ----------
    experiment (array-like): array of experiment values
    predictions (array-like): array of predicted values
    
    Returns
    -------
    ndarray: relative error contributions for each point
    
    Raises
    ------
    ValueError: if inputs contain NaN or Inf values, or if sizes mismatch
    TypeError: if inputs cannot be converted to numpy arrays
    """
    experiment = safe_array_conversion(experiment)
    predictions = safe_array_conversion(predictions)
    contributions = npabs(experiment - predictions) / npabs(experiment)

    return contributions

def _compute_nmse(
        predictions: Union[List, ndarray], 
        experiment: Union[List, ndarray]
) -> float:
    """
    Compute Normalized Mean Squared Error.
    
    Parameters
    ----------
    predictions (array-like): array of predicted values
    experiment (array-like): array of experiment values
        
    Returns
    -------
    float: Normalized Mean Squared Error value
        
    Raises
    ------
    ValueError: if inputs contain NaN or Inf values, or if mean of predictions
        or experiment values is zero
    TypeError: if inputs cannot be converted to numpy arrays
    """
    predictions = safe_array_conversion(predictions)
    experiment = safe_array_conversion(experiment)
    
    if len(predictions) != len(experiment):
        raise ValueError(
            f"Size mismatch: predictions has {len(predictions)} elements, "
            f"experiment has {len(experiment)} elements"
        )

    mean_preds = npmean(predictions)
    mean_exps = npmean(experiment)
    
    if abs(mean_preds) < ValidationConstants.ZERO_THRESHOLD \
        or abs(mean_exps) < ValidationConstants.ZERO_THRESHOLD:
        raise ValueError(
            "Mean of predictions or experiment values is too close to zero. "
            "Cannot compute NMSE."
        )
    
    error_squared = (experiment - predictions) ** 2
    result = npmean(error_squared/(mean_preds * mean_exps))

    return float(result)


def _compute_mean_bias(
        predictions: Union[List, ndarray],
        experiment: Union[List, ndarray]
) -> float:
    """
    Compute Mean Geometric Bias.
    
    Parameters
    ----------
    predictions (array-like): array of predicted values
    experiment (array-like): array of experiment values
    Returns
    -------
    float: mean Geometric Bias value
        
    Raises
    ------
    ValueError: if inputs contain non-positive, NaN or Inf values
    TypeError: if inputs cannot be converted to numpy arrays
    """
    # Convert inputs to numpy arrays with validation
    predictions = safe_array_conversion(predictions)
    experiment = safe_array_conversion(experiment)
    
    # Check for size mismatch
    if len(predictions) != len(experiment):
        raise ValueError(
            f"Size mismatch: predictions has {len(predictions)} elements, "
            f"experiment has {len(experiment)} elements")
    
    if any(predictions <= 0) or any(experiment <= 0):
        raise ValueError("All predicted and experiment values must be positive "
                         "to compute geometric bias.")
    
    log_exp = nplog(experiment)
    log_pred = nplog(predictions)
    result = exp(npmean(log_exp) - npmean(log_pred))
    
    return float(result)


def _compute_geometric_variance(
    predictions: Union[List, ndarray],
    experiment: Union[List, ndarray]
) -> float:
    """
    Compute Geometric Variance.
    
    Parameters
    ----------
    predictions (array-like): array of predicted values
    experiment (array-like): array of experiment values

    Returns
    -------
    float: geometric Variance value
        
    Raises
    ------
    ValueError: if inputs contain non-positive, NaN or Inf values
    TypeError: if inputs cannot be converted to numpy arrays
    """
    predictions = safe_array_conversion(predictions)
    experiment = safe_array_conversion(experiment)
    
    if len(predictions) != len(experiment):
        raise ValueError(f"Size mismatch: predictions has {len(predictions)} "
                         f"elements, experiment has {len(experiment)} elements")
    
    if any(predictions <= 0) or any(experiment <= 0):
        raise ValueError("All predicted and experiment values must be positive "
                         "to compute geometric variance.")
    
    log_ratio = nplog(experiment) - nplog(predictions)
    result = exp(npmean(log_ratio ** 2))
    
    return float(result)
