import pandas as pd
from typing import List, Dict, Any


class ReportData:
    def __init__(self, input_: pd.DataFrame) -> None:
        self.__df: pd.DataFrame = input_

    @property
    def df(self) -> pd.DataFrame:
        return self.__df

    @df.setter
    def df(self, dataframe: pd.DataFrame) -> None:
        self.__df = dataframe

    def get_by_transcriber_name(self) -> List[pd.DataFrame]:
        """Creates a list of dataframes, each of which is a
        different configuration of a transformer"""
        return [
            self.get_by("transcriber_name", name)
            for name in self.get("transcriber_name")
        ]

    def get_by(self, column: str, value: str) -> pd.DataFrame:
        """Creates a new dataframe with the rows where the column
        has the given value."""
        return self.df[self.df[column] == value]

    def get(self, column: str) -> pd.DataFrame:
        """Creates a dataframe with the unique values contained
        in the column provided."""
        return self.df[column].unique()

    def group_by_mean(self, column: str) -> pd.DataFrame:
        return self.df.groupby([column]).mean(numeric_only=True)

    def get_configs_dict(self) -> Dict[str, Dict[str, Any]]:
        raw_params = self.df[
            ["transcriber_name", "params"]
        ].drop_duplicates().to_dict(orient="records")

        config: Dict[str, Dict[str, Any]] = {}

        for cfg in raw_params:
            params_ = eval(cfg["params"])
            params_.pop("name")
            name = cfg["transcriber_name"]
            config[name] = params_

        return config

    def rename_columns(self, columns: Dict[str, str]) -> None:
        self.df.rename(
            columns=columns,
            inplace=True,
        )

    def enumerate_index(self) -> None:
        self.df.index = [
            f"{n + 1} {name}"
            for n, name in enumerate(self.df.index.tolist())
        ]
