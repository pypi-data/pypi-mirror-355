#!/usr/bin/env python
from __future__ import annotations

from typing import Any, Dict, List, Literal, Tuple, Union
import torch
import torch.nn as nn
import torch.nn.functional as F

from glap_model.torchtyping import Float, Int
from glap_model.models import audioencoders
from glap_model.models import textencoders
from glap_model.config import GlapTrainConfig


def freeze_model(mdl):
    for param in mdl.parameters():
        param.requires_grad = False
    return mdl


def load_or_download_pretrained_checkpoint(pretrained_url: str) -> Dict[str, Any]:
    if "http" in pretrained_url:
        dmp = torch.hub.load_state_dict_from_url(
            pretrained_url,
            map_location="cpu",
            weights_only=False,
        )
    else:
        dmp = torch.load(pretrained_url, map_location="cpu", weights_only=False)
    return dmp


class GLAP(nn.Module):
    def __init__(
        self,
        audio_encoder: str = "DashengWrapper",
        text_encoder: Literal["TextEncoderSonarWrapper"] = "TextEncoderSonarWrapper",
        audio_encoder_args: Dict[str, Any] = dict(pretrained=True),
        text_encoder_args: Dict[str, Any] = {},
        embed_size: int = 1024,
        freeze: Literal["audio", "text"] | str | None = None,
        use_checkpointing: bool = False,
        **kwargs,  # Dump
    ) -> None:
        super().__init__()
        self.embed_size = embed_size
        # audio encoder
        self.audio_encoder = getattr(audioencoders, audio_encoder)(**audio_encoder_args)
        self.text_encoder = getattr(textencoders, text_encoder)(**text_encoder_args)
        audio_dim = self.audio_encoder.embed_dim
        text_dim = self.text_encoder.embed_dim

        if freeze is not None:
            if "audio" in freeze:
                self.audio_encoder = freeze_model(self.audio_encoder)
            if "text" in freeze:
                self.text_encoder = freeze_model(self.text_encoder)

        self.use_checkpointing = use_checkpointing

        # projections
        self.audio_proj = nn.Sequential(nn.Linear(audio_dim, embed_size), nn.ReLU(), nn.Linear(embed_size, embed_size))
        self.text_proj = nn.Sequential(nn.Linear(text_dim, embed_size), nn.ReLU(), nn.Linear(embed_size, embed_size))

    def encode_audio(self, audio: Float["b t"], audio_length: Int["b"] | None = None) -> torch.Tensor:
        if self.use_checkpointing:
            audio_embeds = torch.utils.checkpoint.checkpoint(
                self.audio_encoder, audio, audio_length, use_reentrant=False
            )
        else:
            audio_embeds = self.audio_encoder(audio, audio_length)
        audio_embeds = F.normalize(self.audio_proj(audio_embeds), dim=-1)
        return audio_embeds

    def encode_text(
        self,
        text: Float["b t"],
        device: torch.device = torch.device("cpu"),
        *,
        source_lang: Literal["eng_Latn"] = "eng_Latn",
    ) -> torch.Tensor:
        text_embeds = self.text_encoder(text, source_lang=source_lang, device=device)
        text_embeds = F.normalize(self.text_proj(text_embeds), dim=-1)
        return text_embeds

    def forward(
        self,
        audio: Float["b t"],
        text: List[str],
        source_lang: Union[None, str] = None,
        audio_length: Int["b"] | None = None,
    ) -> Union[Float["b"], Tuple[Float["b d"], Float["b d"]]]:
        audio_embeds = self.encode_audio(audio, audio_length)
        # Tokenizer should work for all languages in sonar, no need to pass source_language
        # Except we want to do translation
        if source_lang is None:
            source_lang = "eng_Latn"

        text_embeds = self.encode_text(text, source_lang=source_lang, device=audio_embeds.device)
        return audio_embeds, text_embeds

    def score(self, audio_emb, text_emb):
        return 100 * (audio_emb @ text_emb.T)

    # score uses the forward function to directly score a audio/text pair
    def score_forward(self, *args, **kwargs):
        audio_emb, text_emb = self(*args, **kwargs)
        return self.score(audio_emb=audio_emb, text_emb=text_emb)

    @classmethod
    def from_pretrained(cls, pretrained_url: str):
        dmp = load_or_download_pretrained_checkpoint(pretrained_url)
        cfg = GlapTrainConfig(**dmp["config"])
        mdl = globals()[cfg.model](**cfg.model_args)
        mdl.load_state_dict(dmp["model"])
        return cls(config=cfg, model_impl=mdl)


class GLAPInference(nn.Module):
    def __init__(self, model_impl, config: GlapTrainConfig) -> None:
        super().__init__()
        self.model_impl = model_impl
        self.model_impl.eval()
        self.config = config

    def forward(self, *args, **kwargs):
        return self.model_impl(*args, **kwargs)

    def score(self, audio_emb, text_emb):
        return 100 * (audio_emb @ text_emb.T)

    # score uses the forward function to directly score a audio/text pair
    def score_forward(self, *args, **kwargs):
        audio_emb, text_emb = self(*args, **kwargs)
        return self.score(audio_emb=audio_emb, text_emb=text_emb)

    def encode_text(self, *args, **kwargs):
        return self.model_impl.encode_text(*args, **kwargs)

    def encode_audio(self, *args, **kwargs):
        return self.model_impl.encode_audio(*args, **kwargs)

    @classmethod
    def from_pretrained(cls, pretrained_url: str):
        dmp = load_or_download_pretrained_checkpoint(pretrained_url)
        cfg = GlapTrainConfig(**dmp["config"])
        mdl = globals()[cfg.model](**cfg.model_args)
        mdl.load_state_dict(dmp["model"], strict=True)
        return cls(config=cfg, model_impl=mdl)
