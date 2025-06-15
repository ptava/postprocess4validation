from pathlib import Path
from re import compile
from typing import Type, Optional
from numpy import loadtxt

from ..core import (
    OpenFOAMError,
    DirectoryDataLoader,
    FileDataLoader,
    DataSet,
    PointData,
    register_loader,
    file_path,
    dir_path,
)
from .utils import logger, FilePaths


@register_loader(name = "CSVProbes")
class ProbesLoader(FileDataLoader):
    """
    Load CSV probe data from a specified file.
    
    This class extends FileDataLoader to handle the specific format
    of CSV probe data files.
    """
    _PROBE_PATTERN = compile(
        r"# Probe (\d+) \((-?[\d\.]+) (-?[\d\.]+) (-?[\d\.]+)\)"
    )

    def load(self, path: Path) -> DataSet:
        """
        Load CSV probe data from the specified path.
        
        Parameters
        ----------
        path (str): Path to the OpenFOAM postProcessing file.
        
        Returns
        -------
        dataset (DataSet): Returns DataSet object with processed header info.
            Source attribute of the returned DataSet is set to the source of 
            the loader.
        
        Raises
        ------
        OpenFOAMError:  if error occur while processing header.

        """
        # Validate the file path
        path = file_path(path)
        
        # Initialise DataSet object
        dataset = DataSet(source=self.source)

        # Read the CSV file and extract probes info
        try:
            with path.open() as file:
                for line in file:
                    m = self._PROBE_PATTERN.match(line)
                    if not m:
                        continue
                    probe_idx = int(m.group(1))
                    x = float(m.group(2))
                    y = float(m.group(3))
                    z = float(m.group(4))
                    coordinates = (x, y, z)
                    point = PointData(coordinates, {})
                    dataset.add_point(point)
                    logger.debug(
                        f"Added probe point {probe_idx} at coordinates "
                        f"{coordinates}")
        except Exception as e:
            logger.error(f"Failed to load dataset from {path}: {e}")
            raise OpenFOAMError(f"Failed to load dataset from {path}: {e}")

        return dataset


    def extend(self, path: Path, data: DataSet) -> DataSet:
        """
        Extend the existing dataset with data from the specified CSV file.
        
        Parameters
        ----------
        path (str): Path to the CSV file.
        dataset (DataSet): Existing dataset to extend.
        
        Returns
        -------
        DataSet: Extended dataset with new data.
        
        Raises
        ------
        OpenFOAMError: If the file cannot be parsed correctly.
        """
        path = file_path(path)
        field_name = path.name
        logger.debug(f"Extending dataset with field '{field_name}' from {path}")

        # Read the CSV file and extract probes data
        try:
            self._process_probes_data(path, data)
            return data
        except Exception as e:
            logger.error(f"Failed to extend dataset with {path}: {e}")
            raise ValueError(f"Failed to extend dataset with {path}: {e}")

    @staticmethod
    def _process_probes_data(path: Path, dataset: DataSet) -> DataSet:
        """
        Process the probe data from the CSV file and associate it with the dataset
        points.

        Parameters
        ----------
        path (Path): Path to the CSV file.
        dataset (DataSet): The dataset to populate with field values.

        Returns
        -------
        DataSet: The updated dataset with field values associated with points.
        """
        field_name = path.name
        data = loadtxt(path, comments="#", ndmin=2)
        if data.ndim == 0:
            logger.warning(f"No data found in file {path}")
        times = data[:, 0]
        values = data[:, 1:]
        n_points = values.shape[1]
        if n_points != len(dataset):
            raise OpenFOAMError(
                f"Data inconsistency in file {path}: expected "
                f"{len(dataset)} values, got {n_points}.\n"
                "Vector field values are not supported."
            )
        for p_idx, point in enumerate(dataset.points):
            point[field_name] = {
                float(t): float(v) for t, v in zip(times, values[:, p_idx])
            }
        logger.info(f"Loaded {len(dataset)} points from {path}")
        return dataset


@register_loader(name = "OpenFOAMProbes")
class OpenFOAMProbesLoader(DirectoryDataLoader):
    """
    Load OpenFOAM probe data from a specified directory. Probes data typically
    stored in 'postProcessing/<subfolder>/<time_folder>' in files with probes
    value stored for multiple time steps.
    
    This class extends DirectoryDataLoader to handle the specific format
    of OpenFOAM probe data files.

    Arguments
    ---------
    file_loader (Type[FileDataLoader]): Class to load file data.
    source (str): Source of the data.
    subfolder (str): Subfolder name. Default value 'FilePaths.PROBES_SUBFOLDER'.
    time (str): Time step to process. If None, all time steps are processed.
    """
    def __init__(
        self,
        file_loader: Type[FileDataLoader],
        folder: Path,
        source: str,
        subfolder: Optional[str] = None,
        time: Optional[str] = None,
    ):
        super().__init__(file_loader, source, folder)
        self._subfolder = subfolder or FilePaths.PROBES_SUBFOLDER
        self._time = time 

    def load(self, path: Path) -> DataSet:
        """
        Load OpenFOAM probe data from the specified path.
        
        Parameters
        ----------
        path (Path): Path to the main data directory.
        
        Returns
        -------
        dict: Dictionary containing loaded data.
        """
        validated_path = dir_path(path)
        logger.info(f"Finding OpenFOAM data in {validated_path}")

        # Get path of the folder to process
        processing = self.get_processing_folder(
            folder = validated_path,
            subfolder = self.subfolder, 
            time_folder = self.time
        )

        # Get all files in the directory
        try:
            probe_files = [f for f in processing.iterdir() if f.is_file()]
            logger.info(f"Found {len(probe_files)} probe files in {processing}")
        except OSError as e:
            msg = f"Failed to list files in processing {processing}: {e}"
            raise ValueError(msg) from e

        if not probe_files:
            msg = f"No files found in processing: {processing}"
            raise ValueError(msg)

        # Filter files based on the file name
        probes_files_names = [f.name for f in probe_files]
        fields_dict = {name: None for name in probes_files_names}

        # initialise file loader
        file_loader = self.file_loader(source=self.source)

        # Process header info from the first file with 'load' method
        first_file = probe_files[0]
        dataset = file_loader.load(path=first_file)
        dataset.fields.update(fields_dict)

        # Porcess data from all files with 'extend' method
        logger.info(f"Processing data files with: {file_loader.name}")
        for idx, file in enumerate(probe_files):
            try:
                logger.debug(f"Processing probe file {idx+1}/{len(probe_files)}: "
                    f"{file}")
                dataset = file_loader.extend(path=file, data=dataset)
            except Exception as e:
                logger.error(f"Failed to process probe file {file}: {e}")
                raise ValueError(f"Failed to process probe file {file}: {e}")

        # Check consistency between time values in the dataset
        try:
            dataset.check_times()
        except Exception as e:
            logger.error(f"Time consistency check failed: {e}")
            raise ValueError(f"Time consistency check failed: {e}")
            
        if len(dataset) == 0:
            logger.error("No valid data points were extracted from probe files")
            raise ValueError("No valid data points were extracted from probe files")
        
        logger.info(f"Successfully processed {len(dataset)} data points from probe"
                    "files")
        return dataset

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
    def time(self) -> Optional[str]:
        """
        Get the time.
        """
        return self._time

    @time.setter
    def time(self, time: Optional[str]):
        """
        Set the time.
        """
        self._time = time

