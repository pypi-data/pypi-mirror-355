#!/usr/bin/env python3
import torch

from typing import Literal, Sequence
from transformers import AutoTokenizer, AutoModel

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class GTETextEncoder(torch.nn.Module):
    def __init__(
        self,
        model_name: Literal["Alibaba-NLP/gte-large-en-v1.5", "thenlper/gte-base"] = "Alibaba-NLP/gte-large-en-v1.5",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        # print(self.tokenizer)
        self.pad_token_id = self.tokenizer.pad_token_id
        self.embed_dim = self.model.config.hidden_size

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs) -> torch.Tensor:
        with torch.no_grad():
            model_inputs = self.tokenizer(text_input, return_tensors="pt", truncation=True, padding=True)
        model_inputs = model_inputs.to(device)
        embeddings = self.model(**model_inputs)
        mask = (model_inputs.input_ids != self.pad_token_id).unsqueeze(-1).float()
        emb = embeddings.last_hidden_state
        emb = (emb * mask).sum(1) / mask.sum(1)
        return emb


if __name__ == "__main__":
    # mdl = GPT2TextEncoder(model_name='openai-community/gpt2-xl')
    mdl = GTETextEncoder()
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
