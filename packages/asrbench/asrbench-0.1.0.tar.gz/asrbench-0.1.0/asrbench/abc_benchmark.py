import logging
from abc import ABC, abstractmethod
from .transcribers.abc_transcriber import Transcriber
from typing import Dict

logger: logging.Logger = logging.getLogger(__file__)


class BenchmarkABC(ABC):
    """Interface that defines the operation and control of benchmarks."""

    @property
    @abstractmethod
    def transcribers(self) -> Dict[str, Transcriber]:
        """Gets all the transcribers of the class."""
        raise NotImplementedError("Implement transcribers property.")

    @abstractmethod
    def run(self) -> str:
        """Run the transcription with each transcriber for each audio in each
        dataset of the class."""
        raise NotImplementedError("Implement run method.")

    @abstractmethod
    def run_with_transcriber(self, name: str) -> str:
        """Runs the benchmark only with the chosen transcriber."""
        raise NotImplementedError("Implement run with transcriber method.")

    def add_transcriber(self, name: str, transcriber: Transcriber) -> None:
        """Add a transcriber to the class."""
        if not isinstance(transcriber, Transcriber):
            raise ValueError(
                f"Transcriber {name} is not instance of Transcriber.",
            )

        self.transcribers[name] = transcriber

    def remove_transcriber(self, name: str) -> None:
        """Removes the transcriber from the class."""
        if name not in self.transcribers:
            raise KeyError(f"Transcriber {name} does not exists.")

        self.transcribers.pop(name)
