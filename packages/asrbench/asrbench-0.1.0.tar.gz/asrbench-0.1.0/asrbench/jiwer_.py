import jiwer
import re
import unicodedata
from num2words import num2words, CONVERTER_CLASSES
from .transcribe import Measures
from typing import List


class JiwerManager:
    def __init__(self, language: str) -> None:
        self.__lang: str = language

    def normalize_txt(self, txt: str) -> str:
        """Return the post-processed text from jiwer transform"""
        compose: jiwer.Compose = self._create_normalize_transform()
        processed_txt: str = compose(txt)
        return "".join(processed_txt)

    def get_measures(self, reference: str, hypothesis: str) -> Measures:
        """Returns all measures provided by jiwer (wer, cer, mer, wil, wip)"""
        return Measures(
            wer=self.get_wer(reference, hypothesis),
            cer=self.get_cer(reference, hypothesis),
            mer=self.get_mer(reference, hypothesis),
            wil=self.get_wil(reference, hypothesis),
            wip=self.get_wip(reference, hypothesis)
        )

    def get_wer(self, reference: str, hypothesis: str) -> float:
        """Measure Word Error Rate [WER]

        Parameters:
             reference: verified transcript.
             hypothesis: generated transcript.
        """
        return round(
            jiwer.wer(
                reference=reference,
                reference_transform=self._create_default_transform(),
                hypothesis=hypothesis,
                hypothesis_transform=self._create_default_transform()
            ),
            2
        )

    def get_cer(self, reference: str, hypothesis: str) -> float:
        """Measure Character Error Rate [CER].

        Parameters:
            reference: verified transcript.
            hypothesis: generated transcript.
        """
        return round(
            jiwer.cer(
                reference=reference,
                reference_transform=self._create_char_transform(),
                hypothesis=hypothesis,
                hypothesis_transform=self._create_char_transform()
            ),
            2
        )

    def get_mer(self, reference: str, hypothesis: str) -> float:
        """Measure Match Error Rate [MER].

        Parameters:
            reference: verified transcript.
            hypothesis: generated transcript.
        """
        return round(
            jiwer.mer(
                reference=reference,
                reference_transform=self._create_default_transform(),
                hypothesis=hypothesis,
                hypothesis_transform=self._create_default_transform()
            ),
            2
        )

    def get_wil(self, reference: str, hypothesis: str) -> float:
        """Measure Word Information Lost [WIL].

        Parameters:
            reference: verified transcript.
            hypothesis: generated transcript.
        """
        return round(
            jiwer.wil(
                reference=reference,
                reference_transform=self._create_default_transform(),
                hypothesis=hypothesis,
                hypothesis_transform=self._create_default_transform()
            ),
            2
        )

    def get_wip(self, reference: str, hypothesis: str) -> float:
        """Measure Word Information Preserved [WIP].

        Parameters:
            reference: verified transcript.
            hypothesis: generated transcript.
        """
        return round(
            jiwer.wip(
                reference=reference,
                reference_transform=self._create_default_transform(),
                hypothesis=hypothesis,
                hypothesis_transform=self._create_default_transform()
            ),
            2
        )

    def _create_default_transform(self) -> jiwer.Compose:
        return jiwer.Compose(
            [
                jiwer.RemoveEmptyStrings(),
                jiwer.ToLowerCase(),
                jiwer.RemoveMultipleSpaces(),
                jiwer.Strip(),
                jiwer.RemovePunctuation(),
                lambda texts: _normalize_number2word(texts, self.__lang),
                _remove_accents,
                jiwer.ReduceToListOfListOfWords()
            ]
        )

    def _create_char_transform(self) -> jiwer.Compose:
        return jiwer.Compose(
            [
                jiwer.RemoveEmptyStrings(),
                jiwer.ToLowerCase(),
                jiwer.RemoveMultipleSpaces(),
                jiwer.Strip(),
                jiwer.RemovePunctuation(),
                lambda texts: _normalize_number2word(texts, self.__lang),
                _remove_accents,
                jiwer.ReduceToListOfListOfChars()
            ]
        )

    def _create_normalize_transform(self) -> jiwer.Compose:
        return jiwer.Compose(
            [
                jiwer.RemoveEmptyStrings(),
                jiwer.ToLowerCase(),
                jiwer.RemoveMultipleSpaces(),
                jiwer.Strip(),
                jiwer.RemovePunctuation(),
                _remove_accents,
                lambda texts: _normalize_number2word(texts, self.__lang),
            ]
        )


def _normalize_number2word(texts: List[str], lang: str = "en") -> List[str]:
    """Converts numerical digits in the text to their word equivalents.

    Parameters:
        texts : the input text list.
        lang: transcription language.

    Returns:
        the texts with numbers converted to words.
    """

    def replace_number(match: re.Match) -> str:
        number_as_word = num2words(
            int(match.group()),
            lang=lang,
        )

        return number_as_word

    return [re.sub(r'\b\d+\b', replace_number, txt) for txt in texts]


def _remove_accents(texts: List[str]) -> List[str]:
    return [
        ''.join(
            char for char in unicodedata.normalize('NFD', txt)
            if unicodedata.category(char) != 'Mn'
        ) for txt in texts
    ]


def is_language_supported(language: str) -> bool:
    return language in CONVERTER_CLASSES
