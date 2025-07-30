import time
from .dataset import Dataset
from .observer import Observer
from typing import List


class BenchmarkContext:
    """Controls the context and progress of Benchmark execution.

    Arguments:
        datasets: List of datasets in the Benchmark class.
        observer: Observer class to display progress to user.
    """
    def __init__(self, datasets: List[Dataset], observer: Observer) -> None:
        self.__datasets: List[Dataset] = datasets
        self._total_pairs: int = 0
        self._current_pair: int = 0
        self._start: float = 0.0
        self._progress: float = 0.0
        self._observer: Observer = observer
        self.__dataset = None

    @property
    def dataset(self) -> Dataset:
        """Get the dataset currently running."""
        if self.__dataset is None:
            raise ValueError(
                "Context dataset is none, verify benchmark run methods.",
            )

        return self.__dataset

    def set_dataset(self, idx: int) -> None:
        """Defines the dataset to be executed."""
        self.__dataset: Dataset = self.__datasets[idx]
        self._total_pairs = len(self.__dataset.pairs)

    def start_progress(self) -> None:
        """Progress timer starts."""
        self._start: float = time.time()
        self._observer.start_progress()

    def reset_progress(self) -> None:
        """Restarts all execution progress."""
        self._current_pair: int = 0
        self._progress: float = 0.0

    def update_progress(self, transcriber_name: str) -> None:
        """Updates progress status."""
        self._current_pair += 1
        self._observer.update_progress(
            self._calculate_progress(),
            self._get_progress_msg(transcriber_name),
        )

        if self._current_pair == self._total_pairs:
            self._observer.finish()

    def _calculate_progress(self) -> float:
        self._progress = self._current_pair / self._total_pairs
        return self._progress

    def _get_progress_msg(self, transcriber: str) -> str:
        dataset: str = self.__dataset.name
        return f"Processing pairs from {dataset} with {transcriber}."
