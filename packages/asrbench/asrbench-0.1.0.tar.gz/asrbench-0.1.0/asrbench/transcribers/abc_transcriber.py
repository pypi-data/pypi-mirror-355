from abc import ABC, abstractmethod
from typing import Dict, Any


class Transcriber(ABC):
    """Interface to any ASR transcriber."""

    @classmethod
    @abstractmethod
    def from_config(cls, name: str, config: Dict[str, Any]):
        """Create a new Transcriber from a name and configuration Dict.

        Arguments:
            name: Transcriber configuration name.
            config: Dict with Transcriber configuration.
        """
        raise NotImplementedError("Implement from_config method.")

    @property
    @abstractmethod
    def params(self) -> Dict[str, Any]:
        """Parameters passed in the Transcriber configuration."""
        raise NotImplementedError("Implement params property.")

    @property
    @abstractmethod
    def name(self) -> str:
        """Name given to the Transcriber setting in the configuration file."""
        raise NotImplementedError("Implement name property.")

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Transcribes from the path of the audio file provided."""
        raise NotImplementedError("Implement transcribe method.")

    @abstractmethod
    def load(self) -> None:
        """Loads all the instances needed for Transcriber to work into
        memory."""
        raise NotImplementedError("Implement load model method.")

    @abstractmethod
    def unload(self) -> None:
        """Unloads all instances created by Transcriber from memory."""
        raise NotImplementedError("Implement unload model method.")
