import sys
from abc import ABC, abstractmethod


class Observer(ABC):
    """Defines methods to show the status of the benchmark execution
    to the user."""

    @abstractmethod
    def start_progress(self) -> None:
        """Start progress execution."""
        raise NotImplementedError("Implement start_progress method.")

    @abstractmethod
    def update_progress(self, progress: float, message: str) -> None:
        """Updates execution progress.

        Parameters:
            progress:
            message:
        """
        raise NotImplementedError("Implement update_progress method.")

    @abstractmethod
    def notify(self, message: str) -> None:
        """Displays a message to the user."""
        raise NotImplementedError("Implement notify method.")

    @abstractmethod
    def finish(self) -> None:
        """Shows the finalization of progress."""
        raise NotImplementedError("Implement finish method.")


class ConsoleObserver(Observer):
    def start_progress(self) -> None:
        ...

    def update_progress(self, progress: float, message: str) -> None:
        self.__display_message(f"\r[{progress * 100:.2f}%] {message}")

    def notify(self, message: str) -> None:
        self.__display_message(f"{message}")

    def finish(self) -> None:
        self.__display_message("\t Finished.\n")

    @staticmethod
    def __display_message(message: str) -> None:
        sys.stdout.write(message)
        sys.stdout.flush()
