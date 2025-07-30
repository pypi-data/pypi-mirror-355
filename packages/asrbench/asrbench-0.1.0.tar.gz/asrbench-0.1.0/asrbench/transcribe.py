from dataclasses import dataclass
from typing import Dict


@dataclass
class Measures:
    """Defines the structure of Jiwer measures."""
    wer: float
    cer: float
    mer: float
    wil: float
    wip: float


@dataclass
class TranscribeResult:
    """Defines the result structure of transcriptions."""
    audio: str
    asr: str
    transcriber_name: str
    params: Dict[str, str]
    reference: str
    hypothesis: str
    measures: Measures
    audio_duration: float
    runtime: float
    rtf: float
    accuracy: float
    dataset: str

    def to_dict(self) -> Dict[str, any]:
        """Transforms the class structure into a Dict."""
        return {
            "audio": self.audio,
            "asr": self.asr,
            "transcriber_name": self.transcriber_name,
            "params": self.params,
            "reference": self.reference,
            "hypothesis": self.hypothesis,
            "wer": self.measures.wer,
            "cer": self.measures.cer,
            "mer": self.measures.mer,
            "wil": self.measures.wil,
            "wip": self.measures.wip,
            "audio_duration": self.audio_duration,
            "runtime": self.runtime,
            "rtf": self.rtf,
            "accuracy": self.accuracy,
            "dataset": self.dataset,
        }


class TranscribePair:
    """Defines the structure of a data pair for transcription.

    Arguments:
        audio_path: path to the audio file.
        reference: reference transcription.
    """
    def __init__(self, audio_path: str, reference: str) -> None:
        self.__audio: str = audio_path
        self.__reference: str = reference

    @property
    def audio(self) -> str:
        return self.__audio

    @property
    def reference(self) -> str:
        return self.__reference

    def __repr__(self) -> str:
        return f"<TranscribePair audio={self.audio} reference={self.reference}>"
