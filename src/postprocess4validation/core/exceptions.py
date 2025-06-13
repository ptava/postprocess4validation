class PyFoamBaseError(Exception):
    """Root of *all* domain‑specific errors in this package."""
    __slots__ = ("msg",)

    def __init__(self, msg: str | None = None) -> None:
        self.msg = msg or self.__class__.__name__

    def __str__(self) -> str:
        return str(self.msg)


class PointDataError(PyFoamBaseError):
    """Errors that arise from an individual ``PointData`` object."""


class DataSetError(PyFoamBaseError):
    """Errors that arise when several points are considered together."""


class OpenFOAMError(PyFoamBaseError):
    """Errors coming from interaction with OpenFOAM files or utilities."""


class PointTimeConsistencyError(PointDataError):
    """Custom exception for inconsistent time values across fields within a PointData."""
    pass

class TimeConsistencyError(DataSetError):
    """Exception raised when time values are inconsistent between points in a dataset."""
    pass

class MetricsFileError(IOError):
    """Custom exception for errors related to metrics file handling."""
    pass

class HeaderFormatError(ValueError):
    """Custom exception for errors related to CSV header format."""
    pass

class CSVParseError(ValueError):
    """Custom exception for errors during CSV parsing."""
    pass

class NoTimeFolderError(OpenFOAMError):
    """Exception raised when no valid time folder is found."""
    pass
