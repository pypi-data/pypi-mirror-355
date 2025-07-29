#!/usr/bin/env python3
import torch

from typing import Literal, Sequence
from transformers import AutoTokenizer, AutoModel

import os

os.environ["TOKENIZERS_PARALLELISM"] = "true"


class GPT2TextEncoder(torch.nn.Module):
    def __init__(
        self,
        model_name: Literal[
            "openai-community/gpt2",
            "openai-community/gpt2-xl",
            "openai-community/gpt2-large",
            "openai-community/gpt2-medium",
        ] = "openai-community/gpt2",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, attn_implementation="sdpa")
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.pad_token_id = self.tokenizer.eos_token_id
        self.embed_dim = self.model.config.hidden_size

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs) -> torch.Tensor:
        text_input = [text_input_sample + self.tokenizer.eos_token for text_input_sample in text_input]
        model_inputs = self.tokenizer(text_input, return_tensors="pt", padding=True)
        model_inputs = model_inputs.to(device)
        embeddings = self.model(**model_inputs)
        lengths = model_inputs.attention_mask.sum(-1)
        last_timestep = lengths - 1
        emb = embeddings.last_hidden_state
        emb = emb[torch.arange(emb.shape[0]), last_timestep]
        return emb


if __name__ == "__main__":
    # mdl = GPT2TextEncoder(model_name='openai-community/gpt2-xl')
    mdl = GPT2TextEncoder()
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
