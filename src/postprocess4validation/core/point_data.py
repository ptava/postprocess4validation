from typing import Dict, Tuple, Optional, Any, Union, KeysView


from .exceptions import PointTimeConsistencyError
from .utils import (
    logger,
    DefaultValues,
)

class PointData:
    """
    Represents a single data point with coordinates and associated scalar field 
    values over time.

    Attributes
    ----------

    coordinates (tuple (x, y, z)): point's coordinates.
    field (dict, optional): a dictionary storing field data over time with
        structure {field_name: {time: value}} where value is a scalar value.

    """
    def __init__(
            self,
            coordinates: Tuple[float, float, float], 
            fields: Optional[Dict[str, Any]]
        ):
        self._coordinates = coordinates
        self._x = coordinates[0]
        self._y = coordinates[1]
        self._z = coordinates[2]

        # TODO: why did I do this?? for data with no time provided (stupid solution)
        # Handle the case where fields are provided as a single value
        self.fields: Dict[str, float] | Dict[str, Dict[float, Any]]

        # If provided make sure to store point values for specific time value
        self.fields = {
            k: (v if isinstance(v, dict) 
                else {DefaultValues.DEFAULT_TIME_FOR_DATASET: v})
            for k, v in fields.items()
        } if fields is not None else {}

        # Perform an initial time consistency check if fields were provided
        if self.fields:
            try:
                self.get_times() 
            except PointTimeConsistencyError as e:
                logger.warning(f"Initial data for PointData at {coordinates} " \
                    f"has inconsistent times: {e}")


    # --- Methods --- 

    def get_field_value(self, field_name: str, time: float) -> Any:
        """
        Get the value of a specific field at a specific time.

        Parameters
        ----------
        field_name (str): the name of the field.
        time (float): the time step.

        Returns
        -------
        Any: the value of the field at the specified time.

        Raises
        -------
        KeyError: if the field_name or time does not exist.
        """
        try:
            return self.fields[field_name][time]
        except KeyError as e:
            if field_name not in self.fields:
                 raise KeyError(f"Field '{field_name}' not found at point "
                    f"{self.coordinates}.") from e
            else:
                 raise KeyError(f"Time {time} not found for field '{field_name}' "
                    f"at point {self.coordinates}.") from e

    def get_field_timeseries(self, field_name: str) -> Dict[float, Any]:
        """
        Get the entire time series (dictionary of time: value) for a specific field.

        Parameters
        ----------
        field_name (str): the name of the field.

        Returns
        -------
        Dict[float, Any]: a dictionary mapping time steps to values for the 
            specified field.

        Raises
        -------
        KeyError: if the field_name does not exist.
        """
        if field_name not in self.fields:
            raise KeyError(f"Field '{field_name}' not found at point {self.coordinates}.")
        return self.fields[field_name]


    def get_times(self, field_name: Optional[str] = None) -> KeysView[float]:
        """
        Get the time steps available for a specific field or check consistency 
        across all fields.

        If `field_name` is provided, returns the time steps for that field.
        If `field_name` is None, checks if all fields share the exact same set 
            of time steps and returns the common time steps if consistent. 
            Raises PointTimeConsistencyError otherwise.

        Parameters
        ----------
        field_name (str, optional): The name of the field to get time steps for.
            If None, checks consistency across all fields. Defaults to None.

        Returns
        -------
        KeysView[float]: the available time steps for the specified field, or 
            the common time steps if `field_name` is None and times are 
            consistent.

        Raises
        ------
        ValueError: if the point has no fields defined.
        KeyError: if the specified `field_name` does not exist.
        PointTimeConsistencyError: if `field_name` is None and the time steps are 
            not identical across all fields.
        """
        if not self.fields:
            raise ValueError(f"Point at {self.coordinates} has no field data.")

        if field_name is not None:
            if field_name not in self.fields:
                raise KeyError(f"Field '{field_name}' not found at point {self.coordinates}.")
            return self.fields[field_name].keys()
        else:
            # Check consistency across all fields
            field_iterator = iter(self.fields.values())
            try:
                ref_times = set(next(field_iterator).keys())
            except StopIteration:
                 raise ValueError(f"Point at {self.coordinates} has no field data.") 

            for i, field_data in enumerate(field_iterator):
                current_times = set(field_data.keys())
                if current_times != ref_times:
                    field_names = list(self.fields.keys())
                    ref_field_name = field_names[0]
                    current_field_name = field_names[i + 1]
                    raise PointTimeConsistencyError(
                        f"Inconsistent time steps at point {self.coordinates}. "
                        f"Field '{ref_field_name}' times: {ref_times}. "
                        f"Field '{current_field_name}' times: {current_times}."
                    )
            # If loop completes without error, times are consistent
            return self.fields[list(self.fields.keys())[0]].keys()

    # --- Dunder methods --- 

    def __repr__(self) -> str:
        """
        Debugging representation.
        """
        coord_str = "(" \
            f"{self._coordinates[0]}," \
            f"{self._coordinates[1]}," \
            f"{self._coordinates[2]})"
        fields_str = ", ".join([f"{k}: {v}" for k, v in self.fields.items()])
        return f"PointData({coord_str}, {fields_str})"

    def __str__(self) -> str:
        """
        User-friendly representation.
        """
        coord_str = \
            f"x={self._coordinates[0]}," \
            f"y={self._coordinates[1]}," \
            f"z={self._coordinates[2]}"
        fields_str = ", ".join([f"{k}={v}" for k, v in self.fields.items()])
        return f"PointData → {coord_str} | {fields_str}"

    def __getitem__(self, key: Union[str, Tuple[str, float]]) -> Any:

        """

        Allows dictionary-like access to field data.

        Usage:
        - `point["temperature"]` returns the entire time-series of "temperature".
        - `point["temperature", 10]` returns the value at time=10.


        Parameters
        ----------
        key (Union[str, Tuple[str, float]]): either the field name (str) or a 
            tuple of (field_name, time).

        Returns
        -------
        Any: the requested field time-series (dict) or specific values.

        Raises
        -------
        TypeError: if the key is not a string or a tuple of (str, float).
        """
        if isinstance(key, tuple) and len(key) == 2:
            field_key, time_key = key
            if not isinstance(field_key, str) or not isinstance(time_key, (int, float)):
                 raise TypeError(
                    f"Key {key} tuple must be (field_name: str, time: float)"
                    " or a string field name."
                )
            return self.get_field_value(field_key, float(time_key))
        return self.get_field_timeseries(key)

    def __setitem__(self, key: Union[str, Tuple[str, float]], value: Any) -> None:
        """
        Allows dictionary-like setting of field data.

        Usage:
        - `point["temperature", 10] = 305` sets the temperature at time=10 to 305.
        - `point["temperature"] = {0: 300, 10: 305}` sets the entire temperature time series.
        """
        if isinstance(key, tuple) and len(key) == 2:
            field_key, time_key = key
            if not isinstance(field_key, str) or not isinstance(time_key, (int, float)):
                 raise TypeError("Key tuple must be (field_name: str, time: float)")
            if field_key not in self.fields:
                self.fields[field_key] = {}
            self.fields[field_key].setdefault(time_key, value)
        else:
            if not isinstance(value, dict):
                raise TypeError("Field values must be a dictionary with time as keys.")
            self.fields.setdefault(key, value)

    @property
    def coordinates(self) -> Tuple[float, float, float]:
        return self._coordinates

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def z(self) -> float:
        return self._z
