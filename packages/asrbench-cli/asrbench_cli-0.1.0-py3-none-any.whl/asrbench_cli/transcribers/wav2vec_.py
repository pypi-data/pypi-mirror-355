import gc
import logging
from typing import Any, Dict, List

import librosa
import torch
from asrbench.transcribers.abc_transcriber import Transcriber
from asrbench.transcribers.registry import register_transcriber
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

from .configs import Wav2VecCfg, convert_str2dtype

logger: logging.Logger = logging.getLogger(__file__)


@register_transcriber('wav2vec')
class Wav2Vec(Transcriber):
    def __init__(self, cfg: Wav2VecCfg) -> None:
        self.__name: str = cfg.name
        self.__params = cfg.__dict__
        self.__config: Wav2VecCfg = cfg
        self.__model = None
        self.__processor = None

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def from_config(cls, name: str, config: Dict[str, Any]):
        return Wav2Vec(Wav2VecCfg.load(config, name))

    @property
    def params(self) -> Dict[str, Any]:
        return self.__params

    def load(self) -> None:
        self.__model: Wav2Vec2ForCTC = Wav2Vec2ForCTC.from_pretrained(
            pretrained_model_name_or_path=self.__config.model,
            torch_dtype=convert_str2dtype(self.__config.compute_type),
        ).to(self.__config.device)
        logger.info(f'Load {self.name} model')

        self.__processor: Wav2Vec2Processor = (
            Wav2Vec2Processor.from_pretrained(self.__config.model)
        )
        logger.info(f'Load {self.name} processor')

    def unload(self) -> None:
        del self.__model
        logger.info(f'Unload {self.name} model')

        del self.__processor
        logger.info(f'Unload {self.name} processor')

        gc.collect()

    def transcribe(self, audio_path: str) -> str:
        if self.__model is None or self.__processor is None:
            self.load()

        audio, sample_rate = librosa.load(audio_path, sr=16000)
        inputs = self.__processor(
            audio=audio, sampling_rate=16000, padding=True, return_tensors='pt'
        ).input_values

        inputs = inputs.to(self.__config.device)

        with torch.no_grad():
            logits = self.__model(inputs).logits

        predicted_ids: torch.Tensor = torch.argmax(logits, dim=-1)

        transcription: List[str] = self.__processor.batch_decode(predicted_ids)
        return transcription[0]
