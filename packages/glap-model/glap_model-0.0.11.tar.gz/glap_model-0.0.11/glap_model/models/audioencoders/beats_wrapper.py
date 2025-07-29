#!/usr/bin/env python3

import torch
from pathlib import Path
from .beats.BEATs import BEATs, BEATsConfig


class BeatsWrapper(torch.nn.Module):
    def __init__(
        self,
        checkpoint=Path(__file__).parent / "beats" / "BEATs_iter3_plus_AS2M_finetuned_on_AS2M_cpt1.pt",
    ):
        super().__init__()
        # load the fine-tuned checkpoints
        checkpoint = torch.load(checkpoint)
        cfg = BEATsConfig(checkpoint["cfg"])
        mdl_impl = BEATs(cfg)
        mdl_impl.predictor = None
        mdl_impl.load_state_dict(checkpoint["model"])
        self.mdl_impl = mdl_impl
        self.embed_dim = cfg.encoder_embed_dim

    def forward(self, x, input_length=None):
        padding_mask = None
        if input_length is not None:
            padding_mask = torch.arange(x.shape[-1], device=x.device)
            padding_mask = padding_mask > input_length.unsqueeze(-1)
        x = self.mdl_impl.extract_features(x, padding_mask=padding_mask)[0]
        x = x.mean(1)
        return x


__all__ = [BeatsWrapper]


if __name__ == "__main__":
    mdl = BeatsWrapper()
    q = mdl(torch.randn(2, 160000), torch.tensor([160000, 160000]))
    print(q)
