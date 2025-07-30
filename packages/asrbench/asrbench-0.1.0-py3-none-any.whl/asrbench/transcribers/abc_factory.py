from abc import ABC, abstractmethod
from .abc_transcriber import Transcriber
from typing import Dict, Any


class TranscriberFactoryABC(ABC):

    @abstractmethod
    def get_transcriber(self, name: str, cfg: Dict[str, Any]) -> Transcriber:
        """Get Transcriber with config"""
        raise NotImplementedError("Implement get_transcriber method.")

    @abstractmethod
    def from_config(
            self,
            config: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Transcriber]:
        """Set up transcribers dict from transcribers section in config file"""
        raise NotImplementedError("Implement from_config method.")
