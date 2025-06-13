from dataclasses import dataclass, field
from typing import Dict, Set, List, Iterable, Iterator, Tuple
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from numpy import ndarray, asarray

from .point_data import PointData
from .line import Line
from .utils import logger, Info, DefaultValues


@dataclass
class Plane(Iterable[Line]):
    """
    A geometric plane identified by a tag (e.g. XY, XZ, YZ) and a fixed 
    coordinate. It stores time-dependent data along lines and points within that
    plane.

    Attributes:
    -----------
    tag (str): identifier of orthogonal plane ('XY', 'XZ', and 'YZ') with first
        and second plane axis in capital letters
    fixed_coord (float): coordinate value of the plane along orthogonal axis

    Properties:
    -----------
    fields (Set[str]): set of all field names associated with the plane
    locations (List[float]): sorted list of locations of the lines in the plane
    points (List[PointData]): list of points in the plane (PointData objects)
    lines (Dict[str, Line]): dictionary of lines in the plane, indexed by their names
    origin (Tuple): point coordinates that belongs to the plane
    normal (Tuple): normal vector to the plane
    """

    tag: str
    fixed_coord: float

    _fields: Set[str] = field(default_factory=set, init=False, repr=False)
    _locations: Set[float] = field(default_factory=set, init=False, repr=False)
    _points: List[PointData] = field(
        default_factory=list, init=False, repr=False)
    _lines: Dict[str, Line] = field(
        default_factory=dict, init=False, repr=False)
    _origin: Tuple[float, float, float] = field(
        default_factory=tuple, init=False, repr=False)
    _normal: Tuple[float, float, float] = field(
        default_factory=tuple, init=False, repr=False)

    # --- Dunder methods --- #
    def __post_init__(self) -> None:
        if self.tag not in Info.SUPPORTED_PLANE_TAGS:
            raise ValueError(f"Unsupported tag {self.tag!r}; choose from "
                             f"{Info.SUPPORTED_PLANE_TAGS}")
        self._set_origin()
        self._set_normal()

    def __iter__(self) -> Iterator[Line]:
        return iter(self._lines.values())

    def __contains__(self, line: Line) -> bool:
        return isinstance(line, Line) and line.name in self._lines

    def __getitem__(self, key: int) -> Line:
        """Get a line by its index."""
        try:
            return list(self._lines.values())[key]
        except IndexError:
            raise IndexError(f"Index {key} not in plane {str(self)}")

    def __str__(self):
        return f"<Plane {self.tag}@{self.fixed_coord:g}>"

    def __repr__(self):
        preview_limit = 35
        whole = ", ".join(self._lines)
        preview = whole[:preview_limit]
        extra = " ..." if len(whole) > preview_limit else ""
        return (
            f"<Plane {self.tag}@{self.fixed_coord:g} "
            f"({len(self.lines)} lines) [{preview}{extra}]>"
        )

    # --- Public methods --- #
    @property
    def fields(self) -> Set[str]:
        """Return set of all field names associated with the plane."""
        if not self._fields:
            for line in self:
                try:
                    self._fields.update(line.fields)
                except ValueError as e:
                    logger.warning(
                        f"Trying to access fields of {line.name} from {line.sources}"
                        f" but it has no fields: {e}"
                    )
        return self._fields

    @property
    def locations(self) -> List[float]:
        """Return sorted list of locations of the lines in the plane."""
        if not self._locations:
            raise ValueError(
                f"Plane {self.tag}@{self.fixed_coord} has no line positions."
            )
        return sorted(self._locations)

    @property
    def lines(self) -> List[Line]:
        return list(self._lines.values())

    @property
    def points(self) -> List[PointData]:
        return self._points

    @property
    def origin(self) -> Tuple[float, float, float]:
        """Return the origin of the plane."""
        return self._origin

    @property
    def normal(self) -> Tuple[float, float, float]:
        """Return the normal vector of the plane."""
        return self._normal

    def add_field_name(self, field: str) -> None:
        """Store field name that is assiated with plane lines."""
        self._fields.add(field)

    def add_point(self, point: PointData) -> None:
        """Add a point to the plane."""
        if point in self._points:
            raise ValueError(
                f"Point {point.coordinates} already exists in plane "
                f"{self.tag}@{self.fixed_coord}"
            )
        self._points.append(point)
        logger.debug(f"Plane {self.tag}@{self.fixed_coord}: stored point "
                     f"{point.coordinates}")

    def add_location(self, coordinate: float) -> None:
        if coordinate not in self._locations:
            logger.debug(
                f"Plane {self.tag}@{self.fixed_coord}: stored location "
                f" {coordinate}"
            )
        self._locations.add(coordinate)

    def add_line(self, line: Line) -> None:
        """Insert *line*; if a line with the same name exists raise error."""
        if line.name in self._lines:
            raise ValueError(
                f"Line named {line.name!r} already exists in {self}")
        # Add Line obhect to the plane
        self._lines[line.name] = line
        logger.debug(f"Plane {self.tag}@{self.fixed_coord}: stored line "
                     f"{line.name!r} "
                     )

    def remove_line(self, name: str) -> None:
        del self._lines[name]

    def get_line(self, name: str) -> Line:
        return self._lines[name]

    def get_field_values(self, source: str, field: str, time: float) -> Dict[str, ndarray]:
        """ Return a dictionary mapping line names to their field values at a given
        time for a specific source. """
        result: Dict[str, ndarray] = {}
        for line in self:
            try:
                result[line.name] = line.get_field_at(source, field, time)
            except KeyError:
                continue
        return result

    def assign_points_to_lines(self) -> None:
        """
        Assign points to lines based on their coordinates. This method assumes
        that the points are already added to the plane.
        """
        if not self._points:
            raise ValueError(
                f"Plane {self.tag}@{self.fixed_coord} has no points.")

        for point in self._points:
            for line in self:
                line.add_point_if_belong(point)

        for line in self:
            if line.has_data():
                logger.debug(
                    f"Line {line.name!r} with "
                    f"[{len(line.points)}/{len(self.points)}] points:"
                )
                for point in line.points:
                    logger.debug(f"\tPoint {point.coordinates}")

    def add_to_plot(
        self,
        ax: Axes,
        field_name: str,
        last_timestep_only: bool,
        line_marker: str = '-',
        scale: float = 1.0,
        possible_characters: Set = Info.SUPPORTED_CHARACTERS
    ) -> None:
        """
        Plot the data of the plane on the given axes. This method assumes the
        plane 'tag' two-string characters represents first and second axes
        respectively
        """
        def _formatting() -> None:
            chars_not_in_tag = possible_characters - set(self.tag)
            fixed_coord_tag = chars_not_in_tag.pop()
            ax.set_title(
                f"{self.tag} plane at "
                f"{fixed_coord_tag.lower()} = {self.fixed_coord:g}")
            ax.set_xlabel(self.tag[0])
            ax.set_ylabel(self.tag[1])

        def _add_line_points(_line: Line) -> None:
            """
            Due to construction of Plane objects field values are plotted on
            first axis, so we shift position and apply scale parameter to that
            axis (indicated by the plane tag)
            """
            points_first_coordinates = asarray([
                getattr(point, self.tag[0].lower()) for point in _line.points
            ])
            points_second_coordinates = asarray([
                getattr(point, self.tag[1].lower()) for point in _line.points
            ])

            try:
                scaled_field = asarray([
                    point.get_field_value(
                        field_name, DefaultValues.DEFAULT_TIME_FOR_DATASET)
                    for point in _line.points
                ]) * scale
                points_first_coordinates += scaled_field
            except KeyError:
                logger.warning(
                    f"Field {field_name!r} not found in points of "
                    f"{self.tag}@{self.fixed_coord}"
                )

            ax.scatter(
                points_first_coordinates,
                points_second_coordinates,
                color='black',
                marker='x',
            )
            logger.debug(
                f"Line {_line.name}: added {len(_line.points)}"
                f" points data [{field_name!r}]"
            )

        def _add_lines_and_points() -> None:
            for line in self:
                if line.has_data():
                    line.add_to_plot(
                        ax, field_name, last_timestep_only, line_marker, scale
                    )
                    _add_line_points(line)

            logger.debug(
                f"Plane {self.tag}@{self.fixed_coord}: added "
                f"{len(self.lines)} lines [{field_name!r}]"
            )

        def _build_legend() -> None:
            """
            Are we sure this works correctly? Are we preserving colors and labels?
            The answer is no: a line store all values from all sources so each line
            should retain a map s.t. colors -> labels
            """
            legend_data: Dict[Tuple, str] = {}
            for line in self:
                if len(line.colors) != len(line.labels):
                    raise ValueError(
                        f"Line {line.name!r} has mismatched colors and labels "
                        f"lengths: {len(line.colors)} vs {len(line.labels)}."
                    )
                for color, label in zip(line.colors, line.labels):
                    legend_data.setdefault(color, label)

            legend_handles: List[Line2D] = []
            legend_labels: List[str] = []

            # Add scatter handle for 'Experiment' values
            scatter_handle = Line2D(
                [], [], color='black', marker='x', linestyle='None'
            )
            legend_handles.append(scatter_handle)
            legend_labels.append('Experiment')

            # Add line handles for each unique color and label
            for color, label in legend_data.items():
                color_handle = Line2D(
                    [], [], color=color, linestyle=line_marker
                )
                legend_handles.append(color_handle)
                legend_labels.append(label)

            ax.legend(
                legend_handles,
                legend_labels,
                loc='upper left',
                bbox_to_anchor=(1.05, 1),
                borderaxespad=0.0,
                title=field_name,
            )
            logger.debug(
                f"Plane {self.tag}@{self.fixed_coord}: built legend with "
                f"{len(legend_handles)} handles."
            )

        _formatting()
        _add_lines_and_points()
        _build_legend()

    def _set_origin(self) -> None:
        self._origin = (0.0, 0.0, 0.0)

    def _set_normal(self) -> None:
        """Set the normal vector of the plane based on its tag and the
        supported ones."""
        axes = ''.join(sorted(self.tag))  # to hadle both XY and YX tags
        normal_vectors = {
            "XY": (0.0, 0.0, 1.0),
            "XZ": (0.0, 1.0, 0.0),
            "YZ": (1.0, 0.0, 0.0),
        }
        if axes not in normal_vectors:
            raise ValueError(f"Unsupported plane tag {self.tag!r}. "
                             f"Supported tags are {Info.SUPPORTED_PLANE_TAGS}")
        self._normal = normal_vectors[axes]
