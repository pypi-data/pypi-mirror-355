import asrbench.utils as utils
import yaml
from .abc_benchmark import BenchmarkABC
from .benchmark import DefaultBenchmark
from .dataset import Dataset
from datetime import datetime, UTC
from .jiwer_ import JiwerManager, is_language_supported
from pathlib import Path
from .transcribers.abc_transcriber import Transcriber
from .transcribers.abc_factory import TranscriberFactoryABC
from .transcribers.factory import DefaultTranscriberFactory
from .transcribers.registry import load_registers
from .observer import Observer, ConsoleObserver
from .output_ctx import OutputContextABC, CsvOutputContext, JsonOutputContext
from typing import Dict, List, Any


class ConfigLoader:
    """Facade to configure the entire benchmark execution environment.

    Arguments:
        filepath_: path to configuration file.
        factory: factory to set up Transcribers.
        observer: observer to show execution status.
    """

    def __init__(
            self,
            filepath_: str,
            factory: TranscriberFactoryABC = DefaultTranscriberFactory(),
            observer: Observer = ConsoleObserver()
    ) -> None:
        utils.check_path(filepath_)

        self.__path: str = filepath_
        self._observer: Observer = observer
        self.__data: Dict[str, Dict[str, Any]] = self.read_data()
        self.__factory: TranscriberFactoryABC = factory
        self.__output_cfg: Dict[str, str] = self.data.get("output", {})
        self.check_external_transcribers()

    @property
    def data(self) -> Dict[str, Dict[str, Any]]:
        return self.__data

    def read_data(self) -> Dict[str, Any]:
        """Read config data."""
        self._observer.notify("Reading configfile.")

        with open(self.__path, "r") as file:
            config: Dict[str, Any] = yaml.safe_load(file)

        return config

    def check_external_transcribers(self) -> None:
        if "transcriber_dir" in self.data:
            external_path: Path = Path(
                self.get_config_section("transcriber_dir")
            )
            load_registers(external_path)

    def set_up_benchmark(self) -> BenchmarkABC:
        self._observer.notify("Mounting Benchmark.")
        benchmark = DefaultBenchmark(
            datasets=self.get_datasets(),
            transcribers=self.get_transcribers(),
            output=self.get_output(),
            observer=self._observer,
            jiwer_=JiwerManager(language=self.get_language())
        )
        return benchmark

    def get_language(self) -> str:
        language: str = self.data.get("language", "en")

        if not is_language_supported(language):
            raise ValueError(f"Language {language} is not supported.")

        return language

    def get_datasets(self) -> List[Dataset]:
        """Get datasets from the configuration file"""
        if not self.has_dataset():
            raise ValueError("Configfile dont have datasets configuration.")

        return [
            Dataset.from_config(name, config)
            for name, config in self.data.get("datasets").items()
        ]

    def has_dataset(self) -> bool:
        return "datasets" in self.data

    def get_transcribers(self) -> Dict[str, Transcriber]:
        """Get transcribers from the configuration file"""
        return self.__factory.from_config(
            self.get_config_section("transcribers"),
        )

    def get_output(self) -> OutputContextABC:
        """Get output from the configuration file."""
        type_: str = self.get_output_type()

        match type_:
            case "csv":
                return CsvOutputContext(self.get_output_filepath())
            case "json":
                return JsonOutputContext(self.get_output_filepath())
            case _:
                raise ValueError(f"Output type {type_} not supported.")

    def get_output_type(self) -> str:
        return self.__output_cfg.get("type", "csv")

    def set_up_output_filename(self) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        return f"{self.get_output_filename()}_{timestamp}"

    def get_output_filepath(self) -> Path:
        """Set up output filepath from the configuration file."""
        return Path(
            self.get_output_dir()
        ).joinpath(
            self.set_up_output_filename()
        )

    def get_output_dir(self) -> str:
        """Get output dir from the configuration file"""
        return self.__output_cfg.get("dir", Path.cwd())

    def get_output_filename(self) -> str:
        """Get output filename from the configuration file."""
        return self.__output_cfg.get("filename", "asrbench")

    def get_config_section(self, section: str) -> Any:
        """Get the section of the configfile by the name provided."""
        if section not in self.data:
            raise KeyError(f"Configfile dont have {section} section.")
        return self.data[section]

    @staticmethod
    def get_section_value(section: Dict[str, Any], key: str) -> Any:
        """Get the value from the section and key provided."""
        if key not in section or section[key] is None:
            raise KeyError(f"Configfile {section} section missing {key}.")

        return section[key]
