#!/usr/bin/env python3
import torch

from typing import Literal, Sequence
from transformers import AutoTokenizer, AutoModel

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class DebertaTextEncoder(torch.nn.Module):
    def __init__(
        self,
        model_name: Literal["microsoft/deberta-v3-base", "microsoft/deberta-v3-large"] = "microsoft/deberta-v3-base",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(
            model_name,
        )
        self.embed_dim = self.model.config.hidden_size
        self.pad_token_id = self.tokenizer.pad_token_id

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs):
        model_inputs = self.tokenizer(text_input, return_tensors="pt", padding=True)
        model_inputs = model_inputs.to(device)
        embeddings = self.model(**model_inputs)
        mask = (model_inputs.input_ids != self.pad_token_id).unsqueeze(-1).float()
        emb = embeddings.last_hidden_state
        emb = (emb * mask).sum(1) / mask.sum(1)
        return emb


if __name__ == "__main__":
    mdl = DebertaTextEncoder()
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
