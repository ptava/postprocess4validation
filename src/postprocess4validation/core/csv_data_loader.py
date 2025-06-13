from csv import DictReader
from re import compile
from typing import Union, Optional, Tuple
from pathlib import Path

from .data_set import DataSet
from .point_data import PointData
from .data_loader import register_loader, FileDataLoader
from .utils import file_path, logger
from .exceptions import HeaderFormatError, CSVParseError




@register_loader(name = "CSV")
class CSVDataLoader(FileDataLoader):
    """
    CSVDataLoader is a subclass of FileDataLoader that handles loading data 
    from CSV files.
    
    It implements the load method to read a CSV file and convert it into a 
    DataSet object.
    """
    _UM_PATTERN = compile(r"(.+?)\s*[\[\(]([^\]\)]+)[\]\)]")
    _FLOATS_PATTERN = compile(r"^-?\d+,\d+$")

    def __init__(self, source: str):
        super().__init__(source=source)

    def load(self, path: Union[str, Path], delimiter: str = ",") -> DataSet:
        """
        Load data from a CSV file and return a DataSet object.
        
        :param file_path: Path to the CSV file.
        :param source: Source of the data (e.g., 'experiment', 'simulation').
        :return: DataSet object containing the loaded data.
        """
        # Validate the path
        path = file_path(path)
        logger.info(f"Loading data with CSV formatting: {path}")

        # Process the CSV file
        try:
            with path.open("r", newline="") as file:
                reader = DictReader(file, delimiter=delimiter)
                
                if reader.fieldnames is None:
                    raise HeaderFormatError(f"CSV file is missing headers: {path}")
                
                headers = list(reader.fieldnames)
                logger.debug(f"CSV Headers: {headers}")
                
                # Extract coordinate names and units
                coord_header = headers[:3]
                coord_names_and_units = [
                    self.extract_name_and_unit(i) for i in coord_header
                ]
                coords_meta = {name: unit for name, unit in coord_names_and_units}
                logger.debug(f"Resolved coordinate headers: {coords_meta}")

                # Extract field names and units
                fields_header = headers[3:]
                fields_names_and_units = [
                    self.extract_name_and_unit(i) for i in fields_header
                ]
                fields_meta = {name: unit for name, unit in fields_names_and_units}
                logger.debug(f"Resolved field headers: {fields_meta}")

                # Create a DataSet object
                dataset = DataSet(
                    source=self.source,
                    coords=coords_meta,
                    fields=fields_meta,
                )

                logger.info(f"Loaded CSV headers: {headers}")

                for i, row in enumerate(reader):
                    try:
                        coordinates = (
                            self.decimal_str_to_float(row[coord_header[0]]),
                            self.decimal_str_to_float(row[coord_header[1]]),
                            self.decimal_str_to_float(row[coord_header[2]])
                        )
                        fields_values = {
                            list(fields_meta.keys())[id]: self.decimal_str_to_float(row[field])
                            for id, field in enumerate(fields_header)
                        }
                        current_point = PointData(coordinates, fields_values)
                        dataset.add_point(current_point)
                    except (ValueError, KeyError) as e:
                        raise CSVParseError(
                            f"Error parsing row {i+1} ({row}): {e}"
                        ) from e

        except HeaderFormatError as e:
            logger.error(f"Header format error in {path}: {e}")
            raise
        except CSVParseError as e:
            logger.error(f"CSV parsing error in {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading CSV {path}: {e}", exc_info=True)
            raise CSVParseError(f"Failed to load CSV file {path}: {e}") from e
            
        if len(dataset) == 0:
            logger.warning(
                f"No data points loaded from {path}. The file might be "
                f"empty or contain only headers."
            )
        else:
            logger.info(
                f"Successfully loaded {len(dataset)} data points from {path}"
            )
            
        return dataset

    def extend(self, path: Path, data: DataSet) -> DataSet:
        logger.info(
            f"Extending dataset {data.source} with CSV formatting: {path}"
        )
        raise NotImplementedError(
            "Extending CSV data is not implemented. "
            "Please use the 'load' method to load new data."
        )


    @classmethod
    def  extract_name_and_unit(cls, header: str) -> Tuple[str, Optional[str]]:
        """
        Extracts the variable name and unit from a header string.

        :param header: Column name, possibly containing a unit.
        :return: Tuple (name, unit) where unit is None if not found.
        """

        match = cls._UM_PATTERN.match(header)
        if match:
            name, unit = match.groups()
            return name.strip(), unit.strip()
        return header.strip(), None


    @classmethod
    def decimal_str_to_float(cls, value: str) -> float:
        """
        Converts a string with either '.' or ',' as decimal separator to a float 
        using re

        :param value: The string representation of a number.
        :return: The float representation of the number.
        """
        try:
            # Replace only if value contains digits with a comma 
            # "1,23" -> "1.23"
            if cls._FLOATS_PATTERN.match(value):
                value = value.replace(",", ".")
            return float(value)  #
        except ValueError:
            raise ValueError(f"Invalid number format: {value}")
