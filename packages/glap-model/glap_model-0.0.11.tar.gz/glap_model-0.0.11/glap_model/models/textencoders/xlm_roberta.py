#!/usr/bin/env python3
import torch

from typing import Literal, Sequence
from transformers import AutoTokenizer, AutoModel

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class XLMRobertaTextEncoder(torch.nn.Module):
    def __init__(
        self,
        model_name: Literal[
            "FacebookAI/xlm-roberta-base", "FacebookAI/xlm-roberta-large"
        ] = "FacebookAI/xlm-roberta-base",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, attn_implementation="sdpa")
        self.model = AutoModel.from_pretrained(model_name)
        self.embed_dim = self.model.config.hidden_size

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs):
        model_inputs = self.tokenizer(text_input, return_tensors="pt", padding=True)
        model_inputs = model_inputs.to(device)
        embeddings = self.model(**model_inputs)
        return embeddings.pooler_output


if __name__ == "__main__":
    mdl = XLMRobertaTextEncoder()
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
