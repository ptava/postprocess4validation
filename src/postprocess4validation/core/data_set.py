from typing import Dict, List, Tuple, Any, Optional
from numpy import array, mean, min, max

from .exceptions import TimeConsistencyError
from .point_data import PointData
from .line import Line
from .plane_set import PlaneSet
from .utils import logger, DefaultValues


# TODO: should be class PointSet (MutableSet[PointData]]) with membership
# tested by the point’s coordinates and duplicate coordinates are disallowed
# The attributes of DataSet objects are used to do stuff in the code and should
# not be done like that, those info should be recalled in other ways (@property)
class DataSet():
    """
    Represents a dataset containing multiple PointData objects.
    Supports iteration, indexing, field value retrieval and filtering.
    """

    def __init__(
        self,
        source: str,
        points: Optional[List[PointData]] = None,
        coords: Optional[Dict[str, Optional[str]]] = None,
        fields: Optional[Dict[str, str]] = None
    ):
        """
        Initializes the dataset with a list of PointData objects.

        Parameters
        ----------
        source (str): dataset label
        points (list[pointData], optional): list of PointData objects.
        coords (dict, optional): point coordinate units {coord_name : unit}
        fields (dict, optional): point info fields and units {field_name : unit}
        """
        self.source = source
        self._coords = coords if coords is not None else {}
        self._fields = fields if fields is not None else {}

        if points is not None:
            for point in points:
                if not isinstance(point, PointData):
                    raise TypeError(f"All elements must be PointData objects")
        self.points = points if points is not None else []

        # Dictionary for fast coordinate lookup
        self._point_index: dict = {
            point.coordinates: point for point in self.points
        }

        logger.debug(
            f"Initialized {source} DataSet with {len(self.points)} points, "
            f"{len(self.coords)} coordinate dimensions, and "
            f"{len(self.get_all_fields())} fields"
        )

    # --- Methods ---

    def add_point(self, point: PointData) -> None:
        """
        Add a PointData object to the dataset.
        """
        already_existing_points = self._point_index
        if point.coordinates in already_existing_points:
            logger.warning(
                f"Point with coordinates {point.coordinates} already exists in"
                " dataset. This could lead to problems."
            )

        self.points.append(point)
        self._point_index.setdefault(point.coordinates, point)
        logger.debug(
            f"Added point with coordinates {point.coordinates} to dataset")

    def add_field_value(self, field_name: str, time: float, value: Any,
                        point_coordinates: Tuple[float, float, float]) -> None:
        """
        Adds a field value for a specific time to a given point in the dataset. 

        Parameters
        ----------
        field_name (str): Name of the field to add.
        time (float): Time value at which the field value is recorded.
        value (Any): The value to be added.
        point_coordinates (Tuple[float, float, float]): The key used in _point_index 
            to locate the PointData object.
        """
        if point_coordinates not in self._point_index:
            raise KeyError(f"Tag {point_coordinates} not found in dataset.")

        # Retrieve the PointData object
        point = self._point_index[point_coordinates]

        if field_name not in point.fields:
            # Initialize the field dictionary if it does not exist
            point.fields[field_name] = {}

        point.fields[field_name][time] = value  # Assign the value

    def get_point_by_coordinates(
        self,
        coordinates: Tuple[float, float, float]
    ) -> Optional[PointData]:
        """
        Retrieves a PointData object by its coordinates if found otherwhise None.

        Parameters
        ----------
        coordinates (Tuple[float, float, float]): The coordinates of the point 
            to retrieve.
        """
        return self._point_index.get(coordinates, None)

    def filter_by_field(self, field_name: str, threshold: float,
                        time: float = 0) -> List[PointData]:
        """
        Returns points where a field value exceeds a given threshold at a specific time.

        :param field_name: Name of the field to filter on.
        :param threshold: Threshold value.
        :param time: Time value to consider.
        :return: List of PointData objects meeting the condition.
        """
        if field_name not in self.fields:
            raise KeyError(f"Field '{field_name}' not found in dataset.")

        filtered_points = []
        for point in self.points:
            try:
                if point.get_field_value(field_name, time) > threshold:
                    filtered_points.append(point)
            except KeyError:
                # Skip points that don't have this field or time
                continue

        logger.debug(f"Filtered dataset by {field_name} > {threshold} at time {time}: "
                     f"found {len(filtered_points)} points")
        return filtered_points

    def get_all_fields(self) -> List[str]:
        """
        Return all field names in the dataset.
        """
        return list(self.fields.keys())

    def get_all_coordinates(self) -> List[Tuple[float, float, float]]:
        """
        Return all (x, y, z) coordinates in the dataset.
        """
        return list(self._point_index.keys())

    def get_field_values(
        self,
        field_name: str,
        time: float = 0.0,
        point_coordinates: Optional[List[Tuple[float, float, float]]] = None
    ) -> List[Any]:
        """
        Returns all values for a specific field in the dataset at a given time.
        """

        # Check if field is available in dataset
        if field_name not in self.fields:
            raise NameError(f'Field {field_name} not in {self.fields}')

        # Use all points if no specific coordinates are provided
        if point_coordinates is None:
            point_coordinates = list(self._point_index.keys())

        field_values = []
        missing_points = 0

        for coordinates in point_coordinates:
            point = self._point_index.get(coordinates)

            if point is None:
                missing_points += 1
                logger.warning(f"Point with tag {coordinates} not found inside "
                               f"{self.source.upper()} dataset ")
                continue

            try:
                point_field_value = point[field_name, time]
                field_values.append(point_field_value)
            except (KeyError, TypeError):
                logger.error(f"Field {field_name} not found at point {coordinates} "
                             f"at time {time}.")
                continue

        if missing_points > 0:
            logger.warning(
                f"{missing_points} points not found in {self.source.upper()} "
                f"dataset when retrieving {field_name} field values."
            )
        return field_values

    def get_field_statistics(self, field_name: str,
                             time: float = 0) -> Dict[str, float]:
        """
        Returns statistics (min, max, mean, median, std) for a specific field 
        at a given time.
        """
        values = self.get_field_values(field_name, time)
        if not values:
            raise ValueError(
                f"No values found for field {field_name} at time {time}.")

        values_array = array(values)
        statistics = {
            'min': min(values_array),
            'max': max(values_array),
            'mean': mean(values_array),
        }
        logger.debug(
            f"Statistics for field {field_name} at time {time}: {statistics}")
        return statistics

    def check_times(self) -> None:
        """
        Returns all time values inside self.fields dictionary
        make sure that each point has the same time values
        """
        if not self.points:
            raise ValueError(
                f"Cannot check time consistency in empty {self.source} dataset"
            )

        if not self.points[0].fields:
            raise ValueError(
                f"First point in {self.source} dataset has no field data"
            )

        # Get times for the first point
        ref_point = self[0]
        try:
            ref_times = ref_point.get_times()
        except (KeyError, TypeError, TimeConsistencyError) as e:
            logger.error(
                f"Failed to check time consistency in {self.source} dataset for "
                f"first point: {e}"
            )
            raise

        # Check consistency
        for point in self.points[1:]:
            try:
                point_times = point.get_times()
                if point_times != ref_times:
                    raise TimeConsistencyError(
                        f"Time values of point {point} are inconsistent with "
                        f"{ref_point}. Expected: {ref_times}, Found: {point_times}"
                    )
            except (KeyError, TypeError, TimeConsistencyError) as e:
                logger.error(
                    f"Failed to check time consistency in {self.source} dataset for "
                    f"point {point}: {e}"
                )
                raise
        logger.debug(
            f"Time consistency check passed for {len(self.points)} points")
        return None

    def get_all_times(self) -> List[float]:
        """
        Returns all time values inside self.fields dictionary converted to a list
        """
        if not self.points:
            raise ValueError(
                f"Cannot get time values in empty {self.source} dataset"
            )

        if not self.points[0].fields:
            raise ValueError(
                f"First point in {self.source} dataset has no field data"
            )

        # Get times for the first point
        ref_point = self[0]
        try:
            return list(ref_point.get_times())
        except (KeyError, TypeError) as e:
            logger.error(
                f"Failed to get time values in {self.source} dataset for "
                f"first point: {e}"
            )
            raise

    def points_to_planes(
            self,
            flow_direction: str = DefaultValues.FLOW_DIR,
    ) -> PlaneSet:
        """
        Build a class PlaneSet from the points in DataSet.

        Parameters
        ----------
        flow_direction (str): The direction of the flow, used to determine the
            plane tags. Default is 'X'. For a specific flow direction are
            determined the orthoonal planes suitable for plotting the data.

        Returns
        -------
        PlaneSet: A mutable set whose elements are fully populated class Plane
            instances
        """
        def _direction_to_tags(_direction: str) -> List[str]:
            """
            Based on the flow direction, return the tags for the planes
            Parameters
            ----------
            _direction (str): direction of the flow

            Returns
            -------
            list[str]: list of tags for the planes
            """
            match _direction:
                case 'X':
                    return ['XY', 'XZ']
                case 'Y':
                    return ['YX', 'YZ']
                case 'Z':
                    return ['ZX', 'ZY']
                case _:
                    raise ValueError(
                        f"Unsupported flow direction: {_direction}")

        def _tag_to_coordinates(
                _tag: str,
                _coordinates: Tuple[float, float, float]
        ) -> Tuple[float, float]:
            """
            Based on the tag, return the line plane fixed coordinate and the
            line fixed coordinate in the plane.

            Parameters
            ----------
            _tag (str): tag of the plane
            _coordinates (tuple[float, float, float]): coordinates of the point

            Returns
            -------
            float: fixed coordinate of the plane (constant third coordinate)
            float: location of the point in the plane (constant coordinate)
            """
            match _tag:
                case 'XY':
                    return _coordinates[2], _coordinates[0]
                case 'XZ':
                    return _coordinates[1], _coordinates[0]
                case 'YZ':
                    return _coordinates[0], _coordinates[1]
                case _:
                    raise ValueError(f"Unsupported tag: {_tag}")

        # Initialize empty PlaneSet
        planes = PlaneSet()

        # find tags of plottable planes based on the flow direction
        tags = _direction_to_tags(flow_direction)

        for tag in tags:
            # Define all planes parsing all points
            for point in self.points:
                fixed_coord, location = _tag_to_coordinates(
                    tag, point.coordinates)
                plane = planes.get_or_create_plane(tag, fixed_coord)
                plane.add_point(point)
                plane.add_location(location)

            logger.debug(
                f"Created {len(planes)} planes in {tag} for {self.source} dataset"
            )

        # Add lines once collected all planes for the current tag
        for plane in planes:
            tag = plane.tag
            for coord in plane.locations:
                line_obj = Line(
                    tag=tag,
                    plane_position=plane.fixed_coord,
                    line_position=coord
                )
                line_obj.set_line_info(flow_direction)
                plane.add_line(line_obj)

        return planes

    # --- Dunder methods ---

    def __str__(self) -> str:
        """
        User-friendly representation
        """
        output = f'{self.source.upper()} DataSet with {len(self.points)} points'
        if len(self.points) > 0:
            # Show first few points for context
            max_points_to_show = min(3, len(self.points))
            points_preview = '\n'.join(
                str(point) for point in self.points[:max_points_to_show]
            )
            if len(self.points) > max_points_to_show:
                points_preview += "\n... and " + \
                    f"{len(self.points) - max_points_to_show} more points"
            output += f"\n{points_preview}"
        return output

    def __len__(self) -> int:
        """
        Returns the number of points in the dataset.
        """
        return len(self.points)

    def __getitem__(self, index: int) -> PointData:
        """
        Allows indexing into the dataset.
        """
        return self.points[index]

    def __setitem__(self, index: int, point: PointData) -> None:
        """
        Allows set item in dataset
        """
        self.points[index] = point  # Replace the existing point
        self._point_index.setdefault(point.coordinates, point)

    @property
    def fields(self) -> Dict[str, str]:
        """
        Returns the list of field names in the dataset.
        """
        if not self._fields:
            fields_set = set(field for point in self.points for field in point.fields)
            self._fields = {
                field: '' for field in fields_set
            }
        return self._fields

    @property
    def coords(self) -> Dict[str, Optional[str]]:
        """
        Returns the list of coordinate names in the dataset.
        """
        return self._coords
