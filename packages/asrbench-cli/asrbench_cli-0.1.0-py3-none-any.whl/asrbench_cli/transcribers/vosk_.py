import gc
import json
import logging
from typing import Any, Dict

import librosa
import numpy as np
from asrbench.transcribers.abc_transcriber import Transcriber
from asrbench.transcribers.registry import register_transcriber
from vosk import KaldiRecognizer, Model

from .configs import VoskCfg

logger: logging.Logger = logging.getLogger(__file__)


@register_transcriber('vosk')
class Vosk(Transcriber):
    def __init__(self, cfg: VoskCfg):
        self.__name: str = cfg.name
        self.__params = cfg.__dict__
        self.__config: VoskCfg = cfg
        self.__model = None
        self.__recognizer = None

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def from_config(cls, name: str, config: Dict[str, Any]):
        return Vosk(VoskCfg.load(config, name))

    @property
    def params(self) -> Dict[str, Any]:
        return self.__params

    def load(self) -> None:
        self.__model = Model(
            model_path=self.__config.model,
            lang=self.__config.lang,
        )
        logger.info(f'Load {self.name} model')

        self.__recognizer = KaldiRecognizer(self.__model, 16000)
        logger.info(f'Load {self.name} recognizer')

    def unload(self) -> None:
        del self.__model
        logger.info(f'Unload {self.name} model')

        del self.__recognizer
        logger.info(f'Unload {self.name} recognizer')
        gc.collect()

    def transcribe(self, audio_path: str) -> str:
        if self.__model is None or self.__recognizer is None:
            self.load()

        audio, sample_rate = librosa.load(audio_path, sr=16000)
        audio_int16 = (audio * 32767).astype(np.int16).tobytes()

        recognizer = KaldiRecognizer(self.__model, sample_rate)
        recognizer.AcceptWaveform(audio_int16)

        final_result = json.loads(recognizer.FinalResult())

        return final_result['text']
