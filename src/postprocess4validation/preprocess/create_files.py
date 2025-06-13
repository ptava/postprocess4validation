from __future__ import annotations
from typing import List, Tuple
from pathlib import Path

from ..core import Line, PlaneSet


_HEADER = """\
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  ...                                   | 
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
"""

def _format_list(lst: List[str]) -> str:
    """
    Format a list of strings into a single string.

    Parameters:
    -----------
        lst (list): The list of strings to format.

    Returns:
    --------
        str: The formatted string.
    """
    left_bracket = "("
    separator = " "
    right_bracket = ")"
    return left_bracket + separator.join([str(item) for item in lst]) + right_bracket
    

def create_probes_file(
    file_path: Path,
    fields: List[str],
    coordinates: List[Tuple[float, float, float]],
    format: str
) -> None:
    """
    Create a probes function object file for OpenFOAM.

    Parameters:
    -----------
        file_path (Path): The path to the probes file to be created.
    """
    with open(file_path, 'w') as f:
        f.write(_HEADER)
        f.write("probes\n")
        f.write("{\n")
        f.write("\ttype               probes;\n")
        f.write("\tlibs               (\"libsampling.so\");\n")
        f.write(f"\tsetFormat          {format};\n")
        f.write(f"\tfields             {_format_list(fields)};\n")
        f.write("\tprobeLocations\n")
        f.write("\t(\n")
        for coord in coordinates:
            f.write(f"\t\t({coord[0]} {coord[1]} {coord[2]})\n")
        f.write("\t);\n")
        f.write("}\n")


def create_lines_file(
    file_path: Path,
    planes: PlaneSet,
    fields: List[str],
    format: str,
    n_points: int,
    min: Tuple[float, float, float],
    max: Tuple[float, float, float],
    type: str = "uniform",
) -> None:
    """
    Create a lines function object file for OpenFOAM.

    Parameters:
    -----------
        file_path (Path): The path to the lines file to be created.
    """
    def _get_min_max_points(
        line: Line,
        min: Tuple[float, float, float],
        max: Tuple[float, float, float]
    ) -> Tuple[str, str]:
        """
        Get the start and end points of a line based on its axis and limits.

        Parameters:
        -----------
            line (Line): The line object containing axis information.
            min (Tuple[float, float, float]): Minimum coordinates.
            max (Tuple[float, float, float]): Maximum coordinates.

        Returns:
        --------
            Tuple[str, str]: Formatted start and end points as strings.
        """
        match line.axis:
            case "X":
                start_point = f"({min[0]} {line.y} {line.z})"
                end_point = f"({max[0]} {line.y} {line.z})"
            case "Y":
                start_point = f"({line.x} {min[1]} {line.z})"
                end_point = f"({line.x} {max[1]} {line.z})"
            case "Z":
                start_point = f"({line.x} {line.y} {min[2]})"
                end_point = f"({line.x} {line.y} {max[2]})"
            case _:
                raise ValueError(f"Invalid axis: {line.axis}. Must be 'X', 'Y', or 'Z'.")

        return start_point, end_point
    
    with open(file_path, 'w') as f:
        f.write(_HEADER)
        f.write("lines\n")
        f.write("{\n")
        f.write("\ttype               sets;\n")
        f.write("\tlibs               (\"libsampling.so\");\n")
        f.write(f"\tsetFormat          {format};\n")
        f.write(f"\tfields             {_format_list(fields)};\n")
        f.write(f"\tsets\n")
        f.write("\t{\n")
        for plane in planes:
            f.write(f"\n\t\t// Lines for plane {plane}\n")
            for line in plane.lines:
                start_point, end_point = _get_min_max_points(line, min, max)
                f.write(f"\t\t{line.name}\n")
                f.write("\t\t{\n")
                f.write(f"\t\t\ttype               {type};\n")
                f.write(f"\t\t\taxis               {line.axis.lower()};\n")
                f.write(f"\t\t\tstart              {start_point};\n")
                f.write(f"\t\t\tend                {end_point};\n")
                f.write(f"\t\t\tnPoints            {n_points};\n")
                f.write("\t\t}\n")
        f.write("\t}\n")
        f.write("}\n")
