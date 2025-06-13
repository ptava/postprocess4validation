from matplotlib.axes import Axes
from typing import Dict, Any, Optional

class AxesWithPlotData(Axes):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._plot_data : Optional[Dict[str, Any]] = None

    @property
    def plot_data(self) -> Dict[str, Any]:
        """
        Get the plot additional data associated with this axes.
        
        Returns:
        --------
            Dict[str, Any]: The plot additional data.
        """
        if self._plot_data is None:
            raise ValueError("Plot additional data has not been initialized.")
        return self._plot_data

    @plot_data.setter
    def plot_data(self, data: Dict[str, Any]) -> None:
        """
        Set the plot additional data for this axes.
        
        Parameters:
        ----------
            data (Dict[str, Any]): The plot additional data to set.
        """
        self._plot_data = data
