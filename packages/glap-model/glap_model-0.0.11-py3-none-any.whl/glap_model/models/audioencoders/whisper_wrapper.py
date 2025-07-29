import torch
import torch.nn as nn
from typing import Literal, Optional

# Load model directly
from transformers import WhisperProcessor, WhisperModel


class HF_Whisper_Wrapper(nn.Module):
    def __init__(self, *args, model_name: Literal["openai/whisper-tiny.en"] = "openai/whisper-tiny.en", **kwargs):
        super().__init__()
        model = WhisperModel.from_pretrained(model_name)
        processor = WhisperProcessor.from_pretrained(model_name)
        self.model = model.encoder
        self.processor = processor
        self.embed_dim = self.model.config.hidden_size

    def forward(self, input: torch.Tensor, input_length: Optional[torch.Tensor] = None) -> torch.Tensor:
        input_features = torch.cat(
            [
                self.processor(
                    sample.cpu(),  # bullshit
                    return_tensors="pt",
                    sampling_rate=16000,
                ).input_features
                for sample in input
            ],
            dim=0,
        ).to(input.device)
        outputs = self.model(
            input_features,
        )
        emb = outputs.last_hidden_state
        mask = None
        if input_length is not None:
            input_mask = ((input_length / 16000) * 50).long()
            mask = torch.arange(emb.shape[1], device=input.device) <= input_mask.unsqueeze(-1)
        if mask is not None:
            emb = (emb * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True)
        else:
            emb = emb.mean(1)
        return emb


class Whisper_Wrapper(nn.Module):
    def __init__(
        self, *args, model_type: Literal["tiny", "small", "medium", "large", "turbo", "base"] = "base", **kwargs
    ):
        super().__init__()
        import whisper

        self.length = int(16000 * 30)
        self.embed_dim = 512
        self.pad_or_trim = whisper.pad_or_trim
        self.log_mel_spectrogram = whisper.log_mel_spectrogram
        model = whisper.load_model(model_type).encoder
        model = model.cpu()
        self.model = model
        self.embed_dim = self.model.ln_post.weight.shape[0]

    def forward(self, input: torch.Tensor, input_length: Optional[torch.Tensor] = None) -> torch.Tensor:
        audio = self.pad_or_trim(input, length=self.length)
        mel = self.log_mel_spectrogram(audio).to(audio.device)
        embedding = self.model(mel)
        mask = None
        if input_length is not None:
            input_mask = ((input_length / 16000) * 50).long()
            mask = torch.arange(embedding.shape[1], device=input.device) <= input_mask.unsqueeze(-1)
        if mask is not None:
            emb = (embedding * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True)
        else:
            emb = embedding.mean(1)
        return emb


if __name__ == "__main__":
    mdl = Whisper_Wrapper()
    mdl(torch.randn(2, 160000), torch.tensor([16000, 14000]))
