#!/usr/bin/env python3
import torch
import torch.nn as nn

from typing import List, Literal, Optional, Sequence
import fairseq2
from fairseq2.data import read_sequence, Collater
from sonar.inference_pipelines.utils import extract_sequence_batch
from sonar.models.sonar_text import get_sonar_text_encoder_hub
from fairseq2.data.text.tokenizers import get_text_tokenizer_hub


class TextEncoderSonarWrapper(nn.Module):
    def __init__(
        self,
        tokenizer: Literal["text_sonar_basic_encoder"] = "text_sonar_basic_encoder",
        encoder: Literal["text_sonar_basic_encoder"] = "text_sonar_basic_encoder",
        max_seq_len: Optional[int] = None,
    ):
        super().__init__()
        fairseq2.setup_fairseq2()

        self.tokenizer = get_text_tokenizer_hub().load(tokenizer)
        self.model = get_sonar_text_encoder_hub().load(encoder)
        self.embed_dim = self.model.encoder.model_dim
        self.max_seq_len = self.model.encoder_frontend.pos_encoder.max_seq_len if max_seq_len is None else max_seq_len

    def forward(self, text_input: Sequence[str], device: torch.device, source_lang: str = "eng_Latn") -> torch.Tensor:
        tokenizer_encoder = self.tokenizer.create_encoder(lang=source_lang)

        def truncate(x: torch.Tensor) -> torch.Tensor:
            return x[: self.max_seq_len]

        pipeline = (
            read_sequence(text_input)
            .map(tokenizer_encoder)
            .map(truncate)
            .bucket(len(text_input))
            .map(Collater(self.tokenizer.vocab_info.pad_idx))
            .map(lambda x: extract_sequence_batch(x, device))
            .map(self.model)
            .map(lambda x: x.sentence_embeddings.to(device))
            .and_return()
        )
        results: List[torch.Tensor] = list(iter(pipeline))
        sentence_embeddings = torch.cat(results, dim=0)
        return sentence_embeddings
