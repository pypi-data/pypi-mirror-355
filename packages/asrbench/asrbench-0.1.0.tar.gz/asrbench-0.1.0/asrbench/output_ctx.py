import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, TextIO


def _set_ext(filepath_: Path, ext_: str) -> str:
    return filepath_.with_suffix(ext_).__str__()


class OutputContextABC(ABC):
    @property
    @abstractmethod
    def filepath(self) -> str:
        raise NotImplementedError("Implement filepath property.")

    @property
    @abstractmethod
    def file(self) -> TextIO:
        raise NotImplementedError("Implement file property.")

    @abstractmethod
    def write_row(self, data: Dict[str, Any]) -> None:
        raise NotImplementedError("Implement write_row method.")

    @abstractmethod
    def __enter__(self) -> TextIO:
        raise NotImplementedError("Implement dunder enter method.")

    @abstractmethod
    def __exit__(self, class_, exception_, traceback_) -> None:
        raise NotImplementedError("Implement dunder exit method.")


class CsvOutputContext(OutputContextABC):
    def __init__(self, filepath_: Path, mode: str = "w") -> None:
        self._mode: str = mode
        self._filepath: str = _set_ext(filepath_, ".csv")

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def file(self) -> TextIO:
        return self.__file

    def write_row(self, data: Dict[str, Any]) -> None:
        self._writer.writerow(data)
        self.__file.flush()

    def __enter__(self) -> TextIO:
        self.__file: TextIO = open(self._filepath, self._mode, encoding="utf8")

        fieldnames: List[str] = [
            "audio",
            "asr",
            "transcriber_name",
            "params",
            "reference",
            "hypothesis",
            "audio_duration",
            "runtime",
            "rtf",
            "wer",
            "wil",
            "wip",
            "cer",
            "mer",
            "accuracy",
            "dataset",
        ]

        self._writer: csv.DictWriter = csv.DictWriter(
            self.__file,
            fieldnames=fieldnames,
        )
        self._writer.writeheader()

        return self.__file

    def __exit__(self, class_, exception_, traceback_) -> None:
        if self.__file:
            self.__file.close()

        if exception_ is not None:
            exception_.add_note("Error when create output file for benchmark.")


class JsonOutputContext(OutputContextABC):
    def __init__(
            self, filepath_: Path,
            mode: str = "w",
            indent: int = 4,
    ) -> None:
        self._mode: str = mode
        self._indent: int = indent
        self._data: List[Dict[str, Any]] = []
        self._filepath: str = _set_ext(filepath_, ".json")

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def file(self) -> TextIO:
        return self.__file

    def write_row(self, data: Dict[str, Any]) -> None:
        self._data.append(data)

    def __enter__(self) -> TextIO:
        self.__file: TextIO = open(self._filepath, self._mode, encoding="utf8")
        return self.__file

    def __exit__(self, class_, exception_, traceback_) -> None:
        if self.__file:
            json.dump(self._data, self.__file, indent=self._indent)
            self.__file.close()

        if exception_ is not None:
            exception_.add_note("Error when create output file for benchmark.")
