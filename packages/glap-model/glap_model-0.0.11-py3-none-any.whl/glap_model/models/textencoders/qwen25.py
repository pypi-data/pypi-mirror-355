#!/usr/bin/env python3
import torch

from typing import Literal, Sequence
from transformers import AutoTokenizer, AutoModel

import os

os.environ["TOKENIZERS_PARALLELISM"] = "true"


class Qwen25TextEncoder(torch.nn.Module):
    def __init__(
        self,
        model_name: Literal["Qwen/Qwen2.5-0.5B", "Qwen/2.5-1.5B", "Qwen/2.5-3B"] = "Qwen/Qwen2.5-0.5B",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, attn_implementation="sdpa")
        self.model = AutoModel.from_pretrained(model_name, attn_implementation="sdpa")
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.pad_token_id = self.tokenizer.eos_token_id
        self.embed_dim = self.model.config.hidden_size

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs) -> torch.Tensor:
        text_input = [text_input_sample + self.tokenizer.eos_token for text_input_sample in text_input]
        model_inputs = self.tokenizer(text_input, return_tensors="pt", padding=True)
        model_inputs = model_inputs.to(device)
        lengths = model_inputs.attention_mask.sum(-1)
        embeddings = self.model(**model_inputs)
        last_timestep = lengths - 1
        emb = embeddings.last_hidden_state
        emb = emb[torch.arange(emb.shape[0]), last_timestep]
        return emb


if __name__ == "__main__":
    # mdl = GPT2TextEncoder(model_name='openai-community/gpt2-xl')
    mdl = Qwen25TextEncoder()
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
