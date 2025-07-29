#!/usr/bin/env python3
from typing import Dict, List, Optional, Union
import torch
import torch.nn as nn
from dasheng import dasheng_base


def parse_spectransforms(transforms: Union[List, Dict]):
    import torchaudio.transforms as audio_transforms

    """parse_transforms
    parses the config files transformation strings to coresponding methods

    :param transform_list: String list
    """
    if isinstance(transforms, dict):
        return torch.nn.Sequential(
            *[getattr(audio_transforms, trans_name)(**v) for trans_name, v in transforms.items()]
        )
    elif isinstance(transforms, list):
        return torch.nn.Sequential(
            *[getattr(audio_transforms, trans_name)(**v) for item in transforms for trans_name, v in item.items()]
        )
    else:
        raise ValueError("Transform unknown")


class DashengWrapper(nn.Module):
    def __init__(self, *args, pretrained_from: Optional[str] = None, **kwargs):
        super().__init__()
        spectransforms = None
        if "spectransforms" in kwargs:
            spectransforms = parse_spectransforms(kwargs.pop("spectransforms"))

        self.model = dasheng_base(*args, **kwargs, spectransforms=spectransforms)
        self.embed_dim = self.model.embed_dim
        # Just remove the last output layer
        if pretrained_from is not None:
            print(f"Load pretrained audio encoder model from {pretrained_from}")
            dump = torch.load(pretrained_from, map_location="cpu")
            self.model.load_state_dict(dump["model"], strict=False)
        self.model.outputlayer = torch.nn.Identity()

    def forward(self, input: torch.Tensor, input_length: Optional[torch.Tensor] = None) -> torch.Tensor:
        emb = self.model(input).mean(1)
        return emb


__all__ = [DashengWrapper]
