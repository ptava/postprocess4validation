from typing import Dict, Type, List, Optional, Tuple
from pathlib import Path
from numpy import ndarray, loadtxt
from os import scandir
from re import compile, search

from ..core import (
    FileDataLoader,
    DirectoryDataLoader,
    OpenFOAMError,
    PlaneSet,
    Line,
    register_loader,
    dir_path,
    file_path,
    get_time_subfolders,
)
from .utils import logger, FilePaths


@register_loader("RAWLines")
class LinesDataLoader(FileDataLoader):
    """
    Load raw lines data from a specified file.
    
    This class extends FileDataLoader to handle the specific format
    of raw line data files (arbitrary whitespace-separated values).

    Data loader for raw lines data.
    """
    def __init__(self, source: str):
        super().__init__(source)

    @staticmethod
    def _extract_name_and_fields(name: str) -> Tuple[str, List[str]]:
        """
        Extract field information from the file name. Assumes the file name is
        <line_name>_<field0>_<field1>_..._<fieldN>.<extension>
        
        Notes:
        -----
        _NAME_FIELDS_PATTERN is a regex pattern that matches the line name and
        fields in the file name.
        <line_name> (str): "line_<float/int>_<float/int>"
        <field> (str): only alphabetic characters
        <extension> (str): only alphabetic characters
        """
        _NAME_FIELDS_PATTERN = compile(
            r"(line_-?\d+(?:\.\d+)?_-?\d+(?:\.?\d+)?)"              # name pattern
            "_"
            r"([A-Za-z]+(?:_[A-Za-z]+)*)\.[a-zA-Z]+$"   # fields pattern
        )
        match = search(_NAME_FIELDS_PATTERN, name)
        if match:
            name = match.group(1)
            fields = match.group(2).split("_")
            logger.debug(
                f"Extracted line name: {name}, fields: {fields}"
            )
            return name, fields
        else:
            raise OpenFOAMError(
                f"Could not extract field names from {name}"
            )

    def load(self, path: Path) -> Tuple[str, Dict[str, Dict[str, ndarray]]]:
        """
        Load data from a single file. Since lines file has no header we do not
        process the header.

        Parameters
        ----------
        path (Path): Path to the OpenFOAM postProcessing file.

        Returns
        -------
        Tuple[str, Dict[str, Dict[str, ndarray]]]: Returns a tuple with the
            following structure:
            (line_name, {field: {time: ndarray(shape=(n, 2))}})
        """
        validated_path = file_path(path)
        logger.info(f"Loading data from {validated_path}")

        # Extract data from the file
        data_array = loadtxt(validated_path, delimiter=None, ndmin=2)

        # Extract field information from the file name
        name, fields = self._extract_name_and_fields(validated_path.name)

        n_cols = data_array.shape[1]
        if n_cols != len(fields) + 1:
            raise OpenFOAMError(
                f"Number of columns in {validated_path} does not match "
                f"the number of fields. Expected {len(fields) + 1}, "
                f"got {n_cols}"
            )

        # Initialize the data dictionary
        data = {field: {} for field in fields}

        for idx, field in enumerate(fields):
            # take the first column (coordinates) and the idx+1 column (values)
            data[field][self.source] = data_array[:, [0, idx + 1]]

        return name, data

    def extend(self, path: Path, data: object) -> object:
        """
        Extend method not implemented. This method is not needed for the current
        implementation. The load method already returns the data in the required
        format.
        """
        raise NotImplementedError(
            "Extend method not implemented. This method is not needed for the "
            "current implementation. The load method already returns the data "
            "in the required format."
        )


@register_loader("OpenFOAMLines")
class OpenFOAMLinesLoader(DirectoryDataLoader):
    """
    Load OpenFOAM lines data from a specified directory. Lines data tipically
    stored in 'postPorcessing/<subfolder>/<time_folder>/lines' directory.
    
    This class extends DirectoryDataLoader to handle the specific format
    of OpenFOAM line data files.

    Attributes
    ----------
    file_loader (Type[FileDataLoader]): Class to load file data
    source (str): Source of the data (e.g., test case directory name)
    folder (Optional, path): Path to the main folder of lines data
    time (Optional, str): Specific time step to process; if None, all time 
        steps are processed

    """
    # TODO: add property for folder_path that can be passed and validated in
    # initialisation (main folder path, i.e path/to/postProcessing)
    def __init__(
        self,
        file_loader: Type[FileDataLoader],
        folder: Path,
        source: str,
        plane_set: Optional[PlaneSet] = None,
        time: Optional[str] = None,
        subfolder: Optional[str] = None,
    ):
        self._plane_set = plane_set
        self._subfolder = subfolder or FilePaths.LINES_SUBFOLDER
        super().__init__(file_loader, source, folder)

    def load(self, path: Path) -> None:
        """
        Load data from a directory modifying the PlaneSet object.

        Parameters
        ----------
        path (Path): Path to the OpenFOAM postProcessing directory.

        Returns
        -------
        PlaneSet: the updated PlaneSet object with the loaded data.

        """
        validated_path = dir_path(path)
        processing_folder = validated_path / self.subfolder
        logger.info(f"Finding OpenFOAM lines data in {validated_path}")

        # Get all subfolders names in the specified directory
        times = self.get_dirs(processing_folder)

        # Collect all files in the subfolders (i.e. time dirs)
        lines_files: Dict[str, List[Path]] = {}
        for time in times:
            lines_files.update(self._collect_files(processing_folder, time))

        # Cache line objects by name avoiding redundant lookups
        lines_cache: Dict[str, Line] = {}

        # Access each file in the lines_files dictionary: load and store data
        for time, files in lines_files.items():
            for file in files:
                loader = self.file_loader(source=time) # pass time as source
                try:
                    name, file_data = loader.load(file)
                    line = lines_cache.get(name)

                    if line is None:
                        line = self.plane_set.get_line_by_name(name)
                        lines_cache[name] = line # naming unambiguous

                    # Add to line processsed data
                    line.update_with_data(
                        source=self.source, 
                        data=file_data
                    )

                except (OpenFOAMError, KeyError) as e:
                    raise OpenFOAMError(f"Error loading data from {file}: {e}")

        return None

    @staticmethod
    def _collect_files(folder: Path, subfolder: str) -> Dict[str, List[Path]]:
        """
        Collect all the files in the sub directories (i.e. time dirs) of the 
        specified directory

        Parameters
        ----------
        folder (Path): path to the directory containing the sub directories
        subfolder (str): subfolder name

        Returns
        -------
        Dictionary with the following structure:
        {
            subfolder0 :    [file0, ..., fileN],
            subfolder1 :    [file0, ..., fileN],
            ...
            subfolderM :    [file0, ..., fileN],
        }
        file0, ..., fileN are type Path objects
        """
        files = {}
        processing_folder = folder / subfolder
        if not processing_folder.is_dir():
            raise OpenFOAMError(f"Path {processing_folder} not found")
        for file in scandir(processing_folder):
            if file.is_file():
                files.setdefault(subfolder, []).append(file.path)
            else:
                logger.warning(f'Path {file.path} not a file. Skipping...')
                continue 
        return files
        

    def get_dirs(self, folder: Optional[Path] = None) -> List[str]:
        """
        Get all time subfolders names in the specified directory.

        Returns
        -------
        A list of time subfolder names.
        """
        if folder:
            folder = dir_path(folder)
            return get_time_subfolders(folder)
        return get_time_subfolders(self.folder)

    @property
    def subfolder(self) -> str:
        """
        Get the subfolder.
        """
        return self._subfolder

    @subfolder.setter
    def subfolder(self, subfolder: str):
        """
        Set the subfolder.
        """
        self._subfolder = subfolder

    @property
    def plane_set(self) -> PlaneSet:
        """
        Get the plane set.
        """
        if self._plane_set is None:
            raise ValueError("PlaneSet is not set. Please set it before "
                             "accessing it.")
        if len(self._plane_set) == 0:
            raise ValueError("PlaneSet is empty. Please add planes before "
                             "accessing it.")
        return self._plane_set

    @plane_set.setter
    def plane_set(self, plane_set: PlaneSet):
        """
        Set the plane set.
        """
        self._plane_set = plane_set


