#!/usr/bin/env python3
import torch

from typing import Literal, Sequence
from transformers import AutoTokenizer, AutoModel

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class ClipTextEncoder(torch.nn.Module):
    def __init__(
        self,
        model_name: Literal[
            "openai/clip-vit-base-patch32", "openai/clip-vit-large-patch14-336", "zer0int/CLIP-GmP-ViT-L-14"
        ] = "openai/clip-vit-base-patch32",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        self.model = model.text_model
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.pad_token_id = self.tokenizer.eos_token_id
        self.embed_dim = self.model.config.hidden_size

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs) -> torch.Tensor:
        model_inputs = self.tokenizer(text_input, return_tensors="pt", padding=True)
        model_inputs = model_inputs.to(device)
        input_ids = dict(
            input_ids=model_inputs.input_ids[..., :77], attention_mask=model_inputs.attention_mask[..., :77]
        )
        embeddings = self.model(**input_ids)
        emb = embeddings.pooler_output
        return emb


if __name__ == "__main__":
    # mdl = GPT2TextEncoder(model_name='openai-community/gpt2-xl')
    mdl = ClipTextEncoder()
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
