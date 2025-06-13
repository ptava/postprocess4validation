from __future__ import annotations
from typing import (
    Dict,
    Iterable,
    Tuple,
    Optional,
    MutableSet,
    List,
    Set,
)

from .line import Line
from .plane import Plane
from .utils import logger, DefaultValues


class PlaneSet(MutableSet[Plane]):
    """A set‑like container that guarantees uniqueness on *(tag, fixed_coord)*."""

    def __init__(self, planes: Optional[Iterable[Plane]] = None) -> None:
        self._index: Dict[Tuple[str, float], Plane] = {}
        self._fields: set = set()
        for plane in planes or ():
            self.add(plane)

    # --- Dunder methods --- #
    def __contains__(self, plane: object) -> bool:
        return (
            isinstance(plane, Plane) and self._make_key(plane) in self._index
        )

    def __len__(self) -> int:
        """Number of planes in the set."""
        return len(self._index)

    def __iter__(self):
        return iter(self._index.values())

    def __str__(self) -> str:
        return f"<PlaneSet ({len(self)} planes)>"

    def add(self, value: Plane) -> None:
        key = self._make_key(value)
        if key in self._index:
            raise ValueError(
                f'value {value.tag}@{value.fixed_coord} already in PlaneSet',
            )
        self._index[key] = value
        logger.debug('PlaneSet: added plane %s@%s', *key)

    def discard(self, value: Plane) -> None:
        self._index.pop(self._make_key(value), None)

    def slice(self, start: int, stop: int) -> PlaneSet:
        """
        Return a new PlaneSet containing planes from start to stop indices.
        """
        planes = list(self._index.values())[start:stop]
        return PlaneSet(planes)

    @property
    def fields(self) -> Set[str]:
        """Set of all field names across all planes in the set."""
        if not self._fields:
            for plane in self:
                try:
                    self._fields.update(plane.fields)
                except ValueError as e:
                    logger.warning(
                        f"Trying to access fields of {plane.tag}@{plane.fixed_coord}"
                        f" but it has no fields: {e}"
                    )
        return self._fields

    @staticmethod
    def _make_key(plane: Plane) -> Tuple[str, float]:
        return (plane.tag, plane.fixed_coord)

    def get_or_create_plane(self, tag: str, fixed_coord: float) -> Plane:
        """
        Get a plane by its tag and fixed coordinate, or create it if it doesn't
        exist.
        """
        plane = self.get_plane(tag, fixed_coord)
        if plane is None:
            plane = Plane(tag, fixed_coord)
            self.add(plane)
            logger.debug(f"PlaneSet: created plane {tag}@{fixed_coord}")
        return plane

    def get_plane(self, tag: str, fixed_coord: float) -> Optional[Plane]:
        """Access a plane by its tag and fixed coordinate."""
        try:
            return self._index[(tag, fixed_coord)]
        except KeyError:
            return None

    def get_all_lines(self) -> List[Line]:
        """Get all lines associated with the planes in the set."""
        lines = []
        for plane in self:
            lines.extend(plane.lines)
        return lines

    def get_line_by_name(self, name: str) -> Line:
        """Get a line by its name."""
        for plane in self:
            for line in plane.lines:
                if line.name == name:
                    return line
        raise KeyError(f"Line with name {name!r} not found in PlaneSet.")

    def visualise_planes_and_lines(self) -> None:
        """TO DO: 3D visualization of all planes and lines in the set."""
        pass

    def filter_planes_by_data(
        self,
        min_lines: int = 1,
    ) -> PlaneSet:
        """
        Filter planes based on following criterion:
        - Plane object has at least one line with data in it
        - Each line needs both ntimes and nfields greater than 0
        """
        filtered_planes = []
        for plane in self:
            lines_with_data = sum(line.has_data() for line in plane.lines)
            logger.debug(
                f"Plane {plane.tag}@{plane.fixed_coord}: "
                f"{lines_with_data}/{len(plane.lines)} lines with data"
            )
            if lines_with_data >= min_lines:
                filtered_planes.append(plane)
        logger.info(
            f"PlaneSet: {len(filtered_planes)}/{len(self)} planes with data"
        )

        return PlaneSet(filtered_planes)

    def group_planes_by_tag(
        self,
    ) -> Dict[str, PlaneSet]:
        """
        Filter planes by their tag.

        Returns
        -------
        Dict[str, PlaneSet]: A dictionary where keys are the common tags of the
            planes and values are PlaneSet objects containing planes with that
            tag.

        """
        planes_by_tag: Dict[str, PlaneSet] = {}
        for plane in self:
            tag = plane.tag
            if tag not in planes_by_tag:
                planes_by_tag[tag] = PlaneSet()
            planes_by_tag[tag].add(plane)

        return planes_by_tag
