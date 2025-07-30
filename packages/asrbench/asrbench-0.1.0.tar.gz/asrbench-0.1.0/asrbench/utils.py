import time
from pydub import AudioSegment
from pathlib import Path


def check_path(filepath: str) -> None:
    """Check provided path if something wrong raise error.

    Parameters:
        filepath: path to check.
    """
    if not filepath:
        raise ValueError("Empty path provided.")

    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"File {path.name} in {path} does not exists.")


def get_filename(filepath_: str) -> str:
    """Get filename by path provided.

    Parameters:
        filepath_: entire path to file.

    Returns:
        name of file.
    """
    return Path(filepath_).name


def get_runtime(start: float) -> float:
    """Calculate runtime by start time provided.

    Parameters:
        start: start time in ms.

    Returns:
        time since start in seconds.
    """
    return round(
        (time.time() - start),
        3,
    )


def get_rtf(runtime: float, duration: float) -> float:
    """Calculate Real Time Factor [RTF] in seconds.

    Parameters:
        runtime: time for execution in seconds.
        duration: audio duration in seconds.

    Returns:
        real time factor for data provided.
    """
    rtf: float = runtime / duration
    return round(rtf, 3)


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds.

    Parameters:
        audio_path: path to audio file.

    Returns:
        duration of audio file in seconds.
    """
    audio = AudioSegment.from_wav(audio_path)
    if audio is not None:
        return round(len(audio) / 1000, 3)
