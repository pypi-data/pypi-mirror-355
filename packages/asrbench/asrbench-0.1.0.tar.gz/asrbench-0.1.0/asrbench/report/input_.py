import pandas as pd
from abc import ABC, abstractmethod
from asrbench.utils import check_path


class Input(ABC):
    @property
    @abstractmethod
    def filepath(self) -> str:
        raise NotImplementedError("Implement filepath property.")

    @abstractmethod
    def read_data(self) -> pd.DataFrame:
        raise NotImplementedError("Implement read_data method.")


class JsonInput(Input):
    def __init__(self, filepath_: str) -> None:
        check_path(filepath_)
        self._filepath: str = filepath_

    @property
    def filepath(self) -> str:
        return self._filepath

    def read_data(self) -> pd.DataFrame:
        return pd.read_json(self._filepath)


class CsvInput(Input):
    def __init__(self, filepath_: str) -> None:
        check_path(filepath_)
        self._filepath: str = filepath_

    @property
    def filepath(self) -> str:
        return self._filepath

    def read_data(self) -> pd.DataFrame:
        return pd.read_csv(self._filepath)
