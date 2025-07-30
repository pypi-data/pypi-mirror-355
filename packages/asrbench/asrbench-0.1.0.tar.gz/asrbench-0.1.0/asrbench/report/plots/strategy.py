import seaborn as sns
import pandas as pd
from abc import ABC, abstractmethod
from typing import Optional, Any


class PlotStrategy(ABC):

    @abstractmethod
    def plot(self, df: pd.DataFrame) -> Any:
        raise NotImplementedError("Implement plot method.")


class DispersionPlot(PlotStrategy):
    def __init__(
        self,
        x: str,
        y: str,
        hue: Optional[str],
        legend: bool = True,
        point_size: int = 75,
    ) -> None:
        self._x: str = x
        self._y: str = y
        self._hue: Optional[str] = hue
        self._legend: bool = legend
        self._point_size: int = point_size

    def plot(self, df: pd.DataFrame) -> sns.FacetGrid:
        return sns.relplot(
            data=df,
            x=self._x,
            y=self._y,
            hue=self._hue,
            s=self._point_size,
            legend=self._legend,
        )


class JointPlot(PlotStrategy):
    def __init__(
        self,
        x: str,
        y: str,
        hue: Optional[str],
        kind: str = "scatter",
    ) -> None:
        self.x = x
        self.y = y
        self.hue = hue
        self.kind = kind

    def plot(self, df: pd.DataFrame) -> sns.JointGrid:
        return sns.jointplot(
            data=df,
            x=self.x,
            y=self.y,
            hue=self.hue,
            kind=self.kind,
        )
