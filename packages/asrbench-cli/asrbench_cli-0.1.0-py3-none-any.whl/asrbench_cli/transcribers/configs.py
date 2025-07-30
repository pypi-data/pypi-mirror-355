import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Set

import torch


@dataclass
class TranscriberCFG(ABC):
    """Interface to define the basics of transcriber configuration.

    Attributes:
        model: name/path of the model to use.
        name: transcriber identifier.
    """

    model: str
    name: str

    @classmethod
    @abstractmethod
    def load(cls, data: Dict[str, Any], name: str):
        """Loads the configuration with the data extracted from the
        configuration section of a transcriber.
        """
        raise NotImplementedError('Implement load class method.')


@dataclass
class FWhisperCfg(TranscriberCFG):
    """Implementation of the configuration interface for Faster Whisper."""

    compute_type: str
    device: str
    beam_size: int
    lang: str

    @classmethod
    def load(cls, data: Dict[str, Any], name: str):
        supported: Set[str] = {
            'model',
            'compute_type',
            'beam_size',
            'device',
            'language',
            'asr',
        }
        _check_unsupported(data, supported, name)

        return FWhisperCfg(
            name=name,
            model=get_config_param(data, 'model', name),
            compute_type=get_config_param(data, 'compute_type', name),
            beam_size=get_config_param(data, 'beam_size', name),
            device=get_config_param(data, 'device', name),
            lang=get_config_param(data, 'language', name),
        )


@dataclass
class WhisperCfg(TranscriberCFG):
    """Implementation of the configuration interface for Whisper (by OpenAI)."""

    device: str
    language: str
    fp16: bool

    @classmethod
    def load(cls, data: Dict[str, Any], name: str):
        supported: Set[str] = {
            'model',
            'device',
            'language',
            'fp16',
            'asr',
        }
        _check_unsupported(data, supported, name)

        return WhisperCfg(
            name=name,
            model=get_config_param(data, 'model', name),
            device=get_config_param(data, 'device', name),
            language=get_config_param(data, 'language', name),
            fp16=get_config_param(data, 'fp16', name),
        )


@dataclass
class Wav2VecCfg(TranscriberCFG):
    """Implementation of the configuration interface for
    Wav2Vec (by Hugging Face).
    """

    device: str
    compute_type: str

    @classmethod
    def load(cls, data: Dict[str, Any], name: str):
        supported: Set[str] = {'model', 'device', 'compute_type', 'asr'}
        _check_unsupported(data, supported, name)

        return Wav2VecCfg(
            name=name,
            model=get_config_param(data, 'model', name),
            device=get_config_param(data, 'device', name),
            compute_type=get_config_param(data, 'compute_type', name),
        )


@dataclass
class HFCfg(TranscriberCFG):
    """Implementation of the configuration interface for
    Auto Model from Hugging Face.
    """

    compute_type: str
    device: str

    @classmethod
    def load(cls, data: Dict[str, Any], name: str):
        supported: Set[str] = {'model', 'device', 'compute_type', 'asr'}
        _check_unsupported(data, supported, name)

        return HFCfg(
            name=name,
            model=get_config_param(data, 'model', name),
            device=get_config_param(data, 'device', name),
            compute_type=get_config_param(data, 'compute_type', name),
        )


@dataclass
class VoskCfg(TranscriberCFG):
    """Implementation of the configuration interface for Vosk."""

    lang: str

    @classmethod
    def load(cls, data: Dict[str, Any], name: str):
        supported: Set[str] = {'model', 'language', 'asr'}
        _check_unsupported(data, supported, name)

        return VoskCfg(
            name=name,
            model=get_config_param(data, 'model', name),
            lang=get_config_param(data, 'language', name),
        )


def get_config_param(
        data: Dict[str, Any], param: str, transcriber: str
) -> Any:
    """Get value of the parameter on data and raise a KeyError if the
    parameter not exists or is None.
    """
    if param not in data or data[param] is None:
        raise KeyError(f'Config data of {transcriber} missing {param}.')
    return data[param]


def _check_unsupported(
        config: Dict[str, Any],
        supported: Set[str],
        name: str,
) -> None:
    unsupported: Set[str] = set(config.keys()) - supported
    if unsupported:
        warnings.warn(
            message=f'The following parameters in {name} config are not '
                    f'supported and will be ignored: {' '.join(unsupported)}',
            category=UserWarning,
        )


def convert_str2dtype(dtype_: str) -> torch.dtype:
    match dtype_:
        case 'float64':
            return torch.float64
        case 'float32':
            return torch.float32
        case 'float16':
            return torch.float16
        case 'int64':
            return torch.int64
        case 'int32':
            return torch.int32
        case 'int16':
            return torch.int16
        case 'int8':
            return torch.int8
        case _:
            raise ValueError(f'Torch dtype {dtype_} not supported.')
