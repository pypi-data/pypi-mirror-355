#!/usr/bin/env python3
import torch

from typing import Literal, Sequence
from transformers import AutoTokenizer, AutoModel

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class FlanT5TextEncoder(torch.nn.Module):
    def __init__(self, model_name: Literal["google/flan-t5-base"] = "google/flan-t5-base", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, attn_implementation="sdpa")
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.pad_token_id = self.tokenizer.eos_token_id
        self.embed_dim = self.model.config.hidden_size

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs) -> torch.Tensor:
        model_inputs = self.tokenizer(text_input, return_tensors="pt", padding=True)
        model_inputs = model_inputs.to(device)
        model_inputs["decoder_input_ids"] = model_inputs.input_ids
        embeddings = self.model(**model_inputs)
        mask = (model_inputs.input_ids != self.pad_token_id).unsqueeze(-1).float()
        emb = embeddings.last_hidden_state
        emb = (emb * mask).sum(1) / mask.sum(1)
        return emb


if __name__ == "__main__":
    # mdl = GPT2TextEncoder(model_name='openai-community/gpt2-xl')
    mdl = FlanT5TextEncoder()
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
