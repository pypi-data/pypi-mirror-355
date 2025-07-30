from pathlib import Path
from .transcribe import TranscribePair
from typing import List, Dict


def _get_param(data: Dict[str, str], param: str, name: str) -> str:
    if param not in data or data[param] is None:
        raise KeyError(f"Dataset {name} param {param} is missing.")
    return data[param]


class Dataset:
    """Class representing the structure of a dataset.

    Arguments:
        name: Dataset name.
        audio_dir: Audio directory.
        ref_dir: Reference directory.
    """

    def __init__(
            self,
            name: str,
            audio_dir: str,
            ref_dir: str,
    ):
        self.__name: str = name
        self.__audio_dir: Path = Path(audio_dir)
        self.__ref_dir: Path = Path(ref_dir)
        self.__pairs: List[TranscribePair] = []
        self.get_data()

    @property
    def name(self) -> str:
        """Dataset identifier."""
        return self.__name

    @property
    def pairs(self) -> List[TranscribePair]:
        """Dataset data pairs."""
        return self.__pairs

    def get_data(self) -> None:
        """Set up dataset TranscriberPairs."""
        self.check_directories()
        audio_files: List[Path] = self.get_audio_files()

        for audio_file in audio_files:
            self.pairs.append(
                TranscribePair(
                    audio_path=audio_file.__str__(),
                    reference=self.get_ref_by_audio(audio_file),
                )
            )

    def check_directories(self) -> None:
        """Check if the Dataset directories are valid."""
        self._check_dir(self.__audio_dir)
        self._check_dir(self.__ref_dir)

    def _check_dir(self, dir_: Path) -> None:
        """Check that the directory provided is valid.

        Parameters:
            dir_: directory to be checked.
        """
        if not dir_.is_dir():
            raise ValueError(
                f"Directory {dir_} of "
                f"Dataset {self.name} is not valid."
            )

    def get_audio_files(self) -> List[Path]:
        """It takes all the files from the audio directory.
        If the directory is empty it raises an error."""
        audio_files: List[Path] = list(self.__audio_dir.glob("*"))

        if not audio_files:
            raise ValueError(
                f"Audio directory {self.__audio_dir} of "
                f"dataset {self.name} is empty."
            )

        return audio_files

    def get_ref_by_audio(self, audio: Path) -> str:
        """Fetches the contents of the reference file from the path of
        the audio file.

        Parameters:
            audio: Path for audio file.
        """
        ref_file: Path = self.__ref_dir.joinpath(
            audio.with_suffix(".txt").name,
        )

        if not ref_file.exists():
            raise FileNotFoundError(
                f"Reference file for {audio.name} not exists.",
            )

        return ref_file.open().read()

    @classmethod
    def from_config(cls, name: str, config: Dict[str, str]):
        """Set up Dataset from config Dict in configfile.

        Parameters:
            name: dataset identifier.
            config: dictionary containing the dataset configuration.
        """
        return Dataset(
            name=name,
            audio_dir=_get_param(config, "audio_dir", name),
            ref_dir=_get_param(config, "reference_dir", name)
        )

    def __repr__(self) -> str:
        return f"<Dataset dir={self.__audio_dir} with {len(self.pairs)} pairs.>"
