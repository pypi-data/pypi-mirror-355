import time
import logging
from .jiwer_ import JiwerManager
from . import utils
from .abc_benchmark import BenchmarkABC
from .benchmark_ctx import BenchmarkContext
from .dataset import Dataset
from .transcribe import TranscribeResult, TranscribePair, Measures
from .transcribers.abc_transcriber import Transcriber
from .observer import Observer
from .output_ctx import OutputContextABC
from typing import List, Dict, Any

logger: logging.Logger = logging.getLogger(__file__)


class DefaultBenchmark(BenchmarkABC):
    def __init__(
            self,
            datasets: List[Dataset],
            transcribers: Dict[str, Transcriber],
            output: OutputContextABC,
            observer: Observer,
            jiwer_: JiwerManager,
    ) -> None:
        self.__transcribers: Dict[str, Transcriber] = transcribers
        self.__datasets: List[Dataset] = datasets
        self.__output: OutputContextABC = output
        self._observer: Observer = observer
        self._context: BenchmarkContext = BenchmarkContext(datasets, observer)
        self._jiwer: JiwerManager = jiwer_

    @property
    def transcribers(self) -> Dict[str, Transcriber]:
        return self.__transcribers

    def run(self) -> str:
        with self.__output:
            for idx, dataset in enumerate(self.__datasets):
                logger.info(f"Run benchmark for dataset: {dataset.name}")
                self._context.set_dataset(idx)
                self._process_dataset_with_transcribers()
        return self.__output.filepath

    def run_with_transcriber(self, name: str) -> str:
        with self.__output:
            for idx, dataset in enumerate(self.__datasets):
                logger.info(
                    f"Run benchmark with transcriber: {name}"
                    f"for dataset: {dataset.name}",
                )

                self._context.set_dataset(idx)
                self._process_dataset_pairs(self._get_transcriber(name))
        return self.__output.filepath

    def _process_dataset_pairs(self, transcriber: Transcriber) -> None:
        self._context.start_progress()
        for pair in self._context.dataset.pairs:
            result: TranscribeResult = self._run_transcribe(
                transcriber,
                pair,
            )

            final_result: Dict[str, Any] = result.to_dict()

            self._context.update_progress(transcriber.name)
            self.__output.write_row(final_result)

    def _process_dataset_with_transcribers(self) -> None:
        for _, transcriber in self.transcribers.items():
            transcriber.load()
            self._process_dataset_pairs(transcriber)
            transcriber.unload()
            self._context.reset_progress()

    def _get_transcriber(self, name: str) -> Transcriber:
        if name not in self.__transcribers:
            raise KeyError(f"Transcriber {name} not in benchmark transcribers.")

        return self.__transcribers[name]

    def _run_transcribe(
            self,
            transcriber: Transcriber,
            pair: TranscribePair,
    ) -> TranscribeResult:
        audio_path: str = pair.audio
        reference: str = pair.reference

        logger.debug(
            f"Run {transcriber.__class__.__name__} with audio: {audio_path}",
        )

        start: float = time.time()
        hypothesis: str = transcriber.transcribe(audio_path)
        runtime: float = utils.get_runtime(start)
        duration: float = utils.get_audio_duration(audio_path)

        measures: Measures = self._jiwer.get_measures(reference, hypothesis)

        return TranscribeResult(
            audio=utils.get_filename(audio_path),
            transcriber_name=transcriber.name,
            asr=transcriber.__class__.__name__,
            params=transcriber.params,
            hypothesis=self._jiwer.normalize_txt(hypothesis),
            reference=self._jiwer.normalize_txt(reference),
            measures=measures,
            accuracy=round(((1 - measures.wer) * 100), 2),
            runtime=runtime,
            audio_duration=duration,
            rtf=utils.get_rtf(runtime, duration),
            dataset=self._context.dataset.name,
        )
