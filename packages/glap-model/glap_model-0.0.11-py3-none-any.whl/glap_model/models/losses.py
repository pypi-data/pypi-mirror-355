from __future__ import annotations
from collections import Counter
import torch
import torch.nn as nn
import torch.nn.functional as F
from glap_model.torchtyping import Float
from glap_model.grad_cache.functional import cat_input_tensor, gather_input_tensor


class LossProxy(torch.nn.Module):
    def __init__(self, loss: torch.nn.Module):
        super().__init__()
        self.loss_impl = loss

    def forward(self, audio_embeds: Float["b d"], text_embeds: Float["b d"], filenames: Float["b"] = None) -> Float:
        loss = self.loss_impl(audio_embeds, text_embeds, filenames)
        return loss


class LossProxyDDP(LossProxy):
    @cat_input_tensor
    @gather_input_tensor
    def forward(self, audio_embeds: Float["b d"], text_embeds: Float["b d"], filenames: Float["b"] = None) -> Float:
        return super().forward(audio_embeds=audio_embeds, text_embeds=text_embeds, filenames=filenames)


class LossProxySingleNode(LossProxy):
    @cat_input_tensor
    def forward(
        self, audio_embeds: Float["b d"], text_embeds: Float["b d"], filenames: Float["b"] | None = None
    ) -> Float:
        return super().forward(audio_embeds, text_embeds, filenames)


class SigAudioTextContrastiveLoss(nn.Module):
    def __init__(
        self,
        temperature: float = 0.1,  # Usually the batch size
        bias: float | None = -10.0,
        embed_regularization: bool = True,
    ):
        super().__init__()
        self.temperature = torch.nn.Parameter(torch.tensor(temperature), requires_grad=True)
        self.embed_regularization = embed_regularization
        if bias is not None:
            self.bias = torch.nn.Parameter(torch.tensor(1.0) * bias, requires_grad=True)
        else:
            self.bias = None

    def similarity(self, emb_x: Float["b d"], emb_y: Float["b d"]) -> Float["b b"]:
        with torch.autocast(device_type="cuda", enabled=False):
            return emb_x @ emb_y.t() / self.temperature

    def forward(self, audio_embed, text_embed, filenames=None):
        similarities = self.similarity(audio_embed, text_embed)
        if self.bias is not None:
            similarities += self.bias

        sim_targets = torch.full(similarities.size(), fill_value=-1).to(similarities.device)
        sim_targets.fill_diagonal_(1)

        loss = -F.logsigmoid(similarities * sim_targets).sum() / audio_embed.shape[0]
        if self.embed_regularization:
            loss = (
                loss
                + torch.mean(torch.abs(audio_embed)) / torch.sqrt(torch.sum(audio_embed**2))
                + torch.mean(torch.abs(text_embed)) / torch.sqrt(torch.sum(text_embed**2))
            )

        return loss


class BCEAudioTextContrastiveLoss(nn.Module):
    def __init__(
        self,
        temperature: float = 0.1,  # Usually the batch size
        embed_regularization: bool = True,
    ):
        super().__init__()
        self.temperature = torch.nn.Parameter(torch.tensor(temperature), requires_grad=True)
        self.embed_regularization = embed_regularization

    def similarity(self, emb_x: Float["b d"], emb_y: Float["b d"]) -> Float["b b"]:
        with torch.autocast(device_type="cuda", enabled=False):
            return emb_x @ emb_y.t() / self.temperature

    def forward(self, audio_embed, text_embed, filenames=None):
        sim_a2t = self.similarity(audio_embed, text_embed)
        sim_t2a = self.similarity(text_embed, audio_embed)

        sim_targets = torch.zeros(sim_a2t.size()).to(sim_a2t.device)
        sim_targets.fill_diagonal_(1)

        if filenames is not None:
            counts = Counter(filenames)
            class_weight = torch.tensor([1.0 / counts[fn] for fn in filenames], device=sim_a2t.device)
            sim_targets = sim_targets * torch.diag(class_weight).to(sim_a2t.device)

        loss_a2t = torch.nn.functional.binary_cross_entropy_with_logits(sim_a2t, sim_targets)
        loss_t2a = torch.nn.functional.binary_cross_entropy_with_logits(sim_t2a, sim_targets)

        loss_atc = (loss_a2t + loss_t2a) / 2
        if self.embed_regularization:
            loss_atc = (
                loss_atc
                + torch.mean(torch.abs(audio_embed)) / torch.sqrt(torch.sum(audio_embed**2))
                + torch.mean(torch.abs(text_embed)) / torch.sqrt(torch.sum(text_embed**2))
            )
        return loss_atc


class AudioTextContrastiveLoss(nn.Module):
    def __init__(self, temperature: float = 0.07, embed_regularization: bool = True):
        super().__init__()
        self.temperature = torch.nn.Parameter(torch.tensor(1.0 / temperature).log(), requires_grad=True)
        self.embed_regularization = embed_regularization

    def similarity(self, emb_x: Float["b d"], emb_y: Float["b d"]) -> Float["b b"]:
        with torch.autocast(device_type="cuda", enabled=False):
            return self.temperature.exp() * emb_x @ emb_y.t()

    def forward(self, audio_embed, text_embed, filenames=None):
        sim_a2t = self.similarity(audio_embed, text_embed)
        sim_t2a = self.similarity(text_embed, audio_embed)

        sim_targets = torch.zeros(sim_a2t.size()).to(sim_a2t.device)
        sim_targets.fill_diagonal_(1)
        if filenames is not None:
            counts = Counter(filenames)
            class_weight = torch.tensor([1.0 / counts[fn] for fn in filenames], device=sim_a2t.device)
            sim_targets = sim_targets * torch.diag(class_weight).to(sim_a2t.device)

        loss_a2t = -torch.sum(F.log_softmax(sim_a2t, dim=1) * sim_targets, dim=1).mean()

        loss_t2a = -torch.sum(F.log_softmax(sim_t2a, dim=1) * sim_targets, dim=1).mean()

        loss_atc = (loss_a2t + loss_t2a) / 2
        if self.embed_regularization:
            loss_atc = (
                loss_atc
                + torch.mean(torch.abs(audio_embed)) / torch.sqrt(torch.sum(audio_embed**2))
                + torch.mean(torch.abs(text_embed)) / torch.sqrt(torch.sum(text_embed**2))
            )
        return loss_atc
