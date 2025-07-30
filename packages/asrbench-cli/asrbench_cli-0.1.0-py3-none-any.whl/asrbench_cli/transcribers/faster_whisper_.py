import gc
import logging
from typing import Any, Dict

from asrbench.transcribers.abc_transcriber import Transcriber
from asrbench.transcribers.registry import register_transcriber
from faster_whisper import WhisperModel

from .configs import FWhisperCfg

logger: logging.Logger = logging.getLogger(__file__)


@register_transcriber('faster_whisper')
class FasterWhisper(Transcriber):
    """Implementation of the ASR interface for the Faster Whisper."""

    def __init__(self, cfg: FWhisperCfg):
        self.__model = None
        self.__lang: str = cfg.lang
        self.__name: str = cfg.name
        self.__params: Dict[str, Any] = cfg.__dict__
        self.__config: FWhisperCfg = cfg
        self.__beam_size: int = cfg.beam_size

    @classmethod
    def from_config(cls, name: str, config: Dict[str, Any]):
        return FasterWhisper(FWhisperCfg.load(config, name))

    @property
    def name(self) -> str:
        return self.__name

    @property
    def params(self) -> Dict[str, Any]:
        return self.__params

    @property
    def beam_size(self) -> int:
        return self.__beam_size

    def load(self) -> None:
        self.__model = WhisperModel(
            model_size_or_path=self.__config.model,
            compute_type=self.__config.compute_type,
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

        segments, info = self.__model.transcribe(
            audio=audio_path, beam_size=self.beam_size, language=self.__lang
        )

        return ' '.join([seg.text for seg in segments])
