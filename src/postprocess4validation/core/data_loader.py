from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Union, Dict, List, Type, Optional, TypeVar, Generic
from pathlib import Path

from .utils import LoaderKind, logger, dir_path
from .openfoam_utils import get_latest_time_subfolder


T = TypeVar("T")

class DataLoader(ABC, Generic[T]):
    """
    Abstract base class for data loading operations.

    This class defines the interface that all data loaders must implement,
    ensuring consistency across different data sources and formats.
    """
    def __init__(self, source:str = "unknown"):
        self.source = source
        self._validate_source_name()

    def _validate_source_name(self):
        """Validate the source name."""
        if not isinstance(self.source, str):
            raise ValueError("Source name must be a string.")
        if not self.source:
            raise ValueError("Source name cannot be empty.")

    @abstractmethod
    def load(self, path: Path) -> T:
        """
        Load data from the specified path and return a DataSet.
        
        This is an abstract method that must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class LoaderRegistry:
    """Registry for data loaders."""
    _FILE_LOADERS: Dict[str, Type[FileDataLoader]] = {}
    _DIR_LOADERS: Dict[str, Type[DirectoryDataLoader]] = {}

    @classmethod
    def get_all(cls, loader_type: str) -> Dict:
        """
        Get the appropriate loaders based on the loader type.
        
        :param loader_type: Type of loader (e.g., 'file', 'directory').
        :return: Dictionary of loaders.
        """
        if loader_type == LoaderKind.FILE:
            return cls._FILE_LOADERS
        if loader_type == LoaderKind.DIRECTORY:
            return cls._DIR_LOADERS
        raise ValueError(f"Unknown loader type: {loader_type}")

    @classmethod
    def get(cls, loader_name: str) -> Type[DataLoader]:
        """
        Get a loader by its name.
        
        Parameters
        ----------
        loader_type (str): Type of loader (e.g., 'file', 'directory').
        loader_name (Optional, str): Name of the loader.

        Returns
        -------
        DataLoader: Loader class.

        Raises
        ------
        ValueError: If the loader is not found.
        """

        if loader_name in cls._FILE_LOADERS:
            return cls._FILE_LOADERS[loader_name]
        if loader_name in cls._DIR_LOADERS:
            return cls._DIR_LOADERS[loader_name]

        raise ValueError(f"Loader not found: {loader_name}")

    @staticmethod
    def loader_pair(value: str) -> List[str]:
        """
        Parse a string into a tuple of two loader names.

        Parameters
        ----------
        value (str): string to parse

        Returns
        -------
        List[str]: list of two loader names

        """
        if not ":" in value:
            raise ValueError(f"Invalid loader pair format: {value}")
        split_value = value.split(":")
        if len(split_value) != 2:
            raise ValueError(f"Invalid loader pair format: {value}")
        return split_value


def register_loader(name: str):
    """
    Decorator that register a new loader class and store to LoaderRegistry 
    FILE_LOADERS and DIR_LOADERS.

    Usage
    -----
    @register_loader("csv")
    class CsvLoader(FileDataLoader):
    
    """
    def decorator(cls: Union[type[FileDataLoader], Type[DirectoryDataLoader]]):
        if issubclass(cls, FileDataLoader):
            LoaderRegistry._FILE_LOADERS[name] = cls
        if issubclass(cls, DirectoryDataLoader):
            LoaderRegistry._DIR_LOADERS[name] = cls
        return cls
    return decorator


class FileDataLoader(DataLoader, ABC, Generic[T]):
    """ 
    Base class for loading data from files.

    This class extends the DataLoader class with functionality specific to 
    file-based data sources.
    """
    name: str = "FileDataLoader"

    def __init__(self, source: str = "file"):
        super().__init__(source)

    @abstractmethod
    def load(self, path: Path) -> T:
        """
        Load data from the specified file path and return a DataSet.
        
        This is an abstract method that must be implemented by subclasses.
        """
        raise NotImplementedError(f"Subclasses must implement this method."
                                  f"to load data from {path}")
    @abstractmethod
    def extend(self, path: Path, 
               data: T) -> T:
        """
        Extend the existing dataset with data from the specified file path.
        
        This is an abstract method that must be implemented by subclasses.
        """
        raise NotImplementedError(f"Subclasses must implement this method."
                                  f"to extend data from {path}")


class DirectoryDataLoader(DataLoader, ABC, Generic[T]):
    """ 
    Base class for loading data from directories.

    This class extends the DataLoader class with functionality specific to
    directory-based data sources.
    """
    name: str = "DirectoryDataLoader"

    def __init__(
            self,
            file_loader: Type[FileDataLoader], 
            source: str = "directory",
            folder: Optional[Path] = None,
    ):
        self._file_loader = file_loader
        self._folder = folder if folder else None
        super().__init__(source)

    @abstractmethod
    def load(self, path: Path) -> T:
        """
        Load data from the specified directory path and return a DataSet.
        
        This is an abstract method that must be implemented by subclasses.
        """
        raise NotImplementedError(f"Subclasses must implement this method."
                                  f"to load data from {path}")

    def get_processing_folder(
            self,
            subfolder: str,
            time_folder: Optional[str] = None,
            folder: Optional[Path] = None
    ) -> Path:
        """
        Get the processing folder for a given subfolder and time folder. If no
        time folder is provided, returns the path to the latest time folder.

        Parameters
        ----------
        subfolder (str): The name of the subfolder to search in.
        time_folder (str, optional): The name of the time folder to search in.
            If not provided, the latest time folder will be used.

        Returns
        -------
        Path: The path to the processing folder.
        """
        folder = folder if folder else self.folder
        target_path = folder / subfolder
        if not target_path.exists():
            raise FileNotFoundError(
                f"The specified subfolder '{subfolder}' does not exist in "
                f"{self.folder}."
            )
        resolved_time_folder = time_folder if time_folder \
            else get_latest_time_subfolder(target_path)

        path_to_time_folder = target_path / resolved_time_folder
        if path_to_time_folder.exists():
            return path_to_time_folder
        else:
            logger.warning(
                f"Time folder '{time_folder}' not found in {target_path}."
                f"Using latest time folder instead.")
            default = target_path / get_latest_time_subfolder(target_path)
            return default

    @property
    def folder(self) -> Path:
        """Get the folder path."""
        if self._folder is None:
            raise ValueError("Folder path is not set.")
        return self._folder

    @folder.setter
    def folder(self, folder: Path):
        """Set the folder path."""
        folder = dir_path(folder)
        self._folder = folder

    @property
    def file_loader(self) -> Type[FileDataLoader]:
        """Get the file loader class."""
        if self._file_loader is None:
            raise ValueError("File loader is not set.")
        return self._file_loader

