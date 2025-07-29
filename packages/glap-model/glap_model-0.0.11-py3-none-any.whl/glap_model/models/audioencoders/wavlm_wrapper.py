import torch
import torch.nn as nn
from typing import Literal, Optional

# Load model directly
from transformers import WavLMModel, AutoConfig


class WavLM_Wrapper(nn.Module):
    def __init__(self, *args, model_name: Literal["microsoft/wavlm-base"] = "microsoft/wavlm-base", **kwargs):
        super().__init__()
        config = AutoConfig.from_pretrained(model_name)
        model = WavLMModel.from_pretrained(model_name, config=config)
        self.model = model
        self.embed_dim = self.model.config.hidden_size

    def forward(self, input: torch.Tensor, input_length: Optional[torch.Tensor] = None) -> torch.Tensor:
        emb = self.model(input, output_hidden_states=True, attention_mask=input_length.unsqueeze(-1)).last_hidden_state
        mask = None
        if input_length is not None:
            input_mask = ((input_length / 16000) * 49).long()
            mask = torch.arange(emb.shape[1], device=input.device) <= input_mask.unsqueeze(1)
        if mask is not None:
            emb = (emb * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True)
        else:
            emb = emb.mean(1)
        return emb


if __name__ == "__main__":
    mdl = WavLM_Wrapper()
    y = mdl(torch.randn(1, 16000), torch.tensor([1000]))
    print(y.shape)
