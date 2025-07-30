import gc
import logging
from typing import Any, Dict

import whisper
from asrbench.transcribers.abc_transcriber import Transcriber
from asrbench.transcribers.registry import register_transcriber

from .configs import WhisperCfg

logger: logging.Logger = logging.getLogger(__file__)


@register_transcriber('whisper')
class Whisper(Transcriber):
    def __init__(self, cfg: WhisperCfg):
        self.__name: str = cfg.name
        self.__lang: str = cfg.language
        self.__fp16: bool = cfg.fp16
        self.__model = None
        self.__params = cfg.__dict__
        self.__config: WhisperCfg = cfg

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def from_config(cls, name: str, config: Dict[str, Any]):
        return Whisper(WhisperCfg.load(config, name))

    @property
    def params(self) -> Dict[str, Any]:
        return self.__params

    def load(self) -> None:
        self.__model = whisper.load_model(
            name=self.__config.model,
            device=self.__config.device,
        )
        logger.info(f'Load {self.name} model')

    def unload(self) -> None:
        del self.__model
        logger.info(f'Unload {self.name} model')

        gc.collect()

    def transcribe(self, audio_path: str) -> str:
        if self.__model is None:
            self.load()

        result: Dict[str, Any] = self.__model.transcribe(
            audio=audio_path, language=self.__lang, fp16=self.__fp16
        )

        return result['text']
