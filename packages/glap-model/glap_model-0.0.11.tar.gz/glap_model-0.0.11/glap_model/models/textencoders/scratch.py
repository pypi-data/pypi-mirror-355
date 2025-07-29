#!/usr/bin/env python3
from __future__ import annotations
import torch.nn as nn
import torch.nn.functional as F
import torch
import math
from dataclasses import dataclass

from typing import Sequence
from transformers import AutoTokenizer

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class SelfAttention(nn.Module):
    def __init__(self, config):
        super().__init__()
        assert config.n_embd % config.n_head == 0
        # key, query, value projections for all heads, but in a batch
        self.c_attn = nn.Linear(config.n_embd, 3 * config.n_embd, bias=config.bias)
        # output projection
        self.c_proj = nn.Linear(config.n_embd, config.n_embd, bias=config.bias)
        # regularization
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        self.is_causal = config.is_causal
        self.n_head = config.n_head
        self.n_embd = config.n_embd
        self.dropout = config.dropout
        # flash attention make GPU go brrrrr but support is only in PyTorch >= 2.0
        self.flash = hasattr(torch.nn.functional, "scaled_dot_product_attention")
        if not self.flash:
            print("WARNING: using slow attention. Flash Attention requires PyTorch >= 2.0")
            # causal mask to ensure that attention is only applied to the left in the input sequence

    def forward(self, x, attention_mask=None):
        B, T, C = x.size()  # batch size, sequence length, embedding dimensionality (n_embd)

        # calculate query, key, values for all heads in batch and move head forward to be the batch dim
        q, k, v = self.c_attn(x).split(self.n_embd, dim=2)
        k = k.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)  # (B, nh, T, hs)
        q = q.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)  # (B, nh, T, hs)
        v = v.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)  # (B, nh, T, hs)

        if self.is_causal:
            causal_mask = torch.ones((T, T), device=x.device, dtype=torch.bool).tril(diagonal=0).view(1, 1, T, T)
            if attention_mask is not None:
                attention_mask = attention_mask & causal_mask

        # causal self-attention; Self-attend: (B, nh, T, hs) x (B, nh, hs, T) -> (B, nh, T, T)
        if self.flash:
            # efficient attention using Flash Attention CUDA kernels
            y = torch.nn.functional.scaled_dot_product_attention(
                q, k, v, attn_mask=attention_mask, dropout_p=self.dropout if self.training else 0
            )
        else:
            # manual implementation of attention
            att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
            if self.is_causal:
                causal_mask = torch.ones((T, T), device=x.device, dtype=torch.bool).tril(diagonal=0).view(1, 1, T, T)
                if attention_mask is not None:
                    attention_mask = attention_mask & causal_mask
            if attention_mask is not None:
                att.masked_fill(attention_mask.logical_not(), float("-inf"))
            att = F.softmax(att, dim=-1)
            att = self.attn_dropout(att)
            y = att @ v  # (B, nh, T, T) x (B, nh, T, hs) -> (B, nh, T, hs)
        y = y.transpose(1, 2).contiguous().view(B, T, C)  # re-assemble all head outputs side by side
        # output projection
        y = self.resid_dropout(self.c_proj(y))
        return y


class MLP(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.c_fc = nn.Linear(config.n_embd, config.mlp_factor * config.n_embd, bias=config.bias)
        self.gelu = nn.GELU()
        self.c_proj = nn.Linear(config.mlp_factor * config.n_embd, config.n_embd, bias=config.bias)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x):
        x = self.c_fc(x)
        x = self.gelu(x)
        x = self.c_proj(x)
        x = self.dropout(x)
        return x


class Block(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.ln_1 = nn.LayerNorm(config.n_embd, bias=config.bias)
        self.attn = SelfAttention(config)
        self.ln_2 = nn.LayerNorm(config.n_embd, bias=config.bias)
        self.mlp = MLP(config)

    def forward(self, x, attention_mask=None):
        x = x + self.attn(self.ln_1(x), attention_mask=attention_mask)
        x = x + self.mlp(self.ln_2(x))
        return x


@dataclass
class TextConfig:
    max_seq_len: int = 512
    n_layer: int = 12
    n_head: int = 8
    n_embd: int = 512
    vocab_size: int | None = None
    is_causal: bool = False
    dropout: float = 0.1
    bias: bool = True  #
    mlp_factor: float = 4


class ScratchTextEncoder(torch.nn.Module):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        config = TextConfig(**kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")
        config.vocab_size = len(self.tokenizer)
        self.is_causal = config.is_causal
        self.transformer = nn.ModuleDict(
            dict(
                wte=nn.Embedding(config.vocab_size, config.n_embd),
                wpe=nn.Embedding(config.max_seq_len, config.n_embd),
                drop=nn.Dropout(config.dropout),
                h=nn.ModuleList([Block(config) for _ in range(config.n_layer)]),
                ln_f=nn.LayerNorm(config.n_embd, bias=config.bias),
            )
        )
        self.pad_token_id = self.tokenizer.eos_token_id
        self.embed_dim = config.n_embd

    def forward(self, text_input: Sequence[str], device: torch.device, **kwargs) -> torch.Tensor:
        if self.is_causal:
            text_input = [text_input_sample + self.tokenizer.eos_token for text_input_sample in text_input]
        model_inputs = self.tokenizer(text_input, return_tensors="pt", padding=True)
        model_inputs = model_inputs.to(device)
        input_idx = model_inputs.input_ids
        b, t = model_inputs.input_ids.size()
        pos = torch.arange(0, t, dtype=torch.long, device=device)  # shape (t)
        tok_emb = self.transformer.wte(input_idx)  # token embeddings of shape (b, t, n_embd)
        pos_emb = self.transformer.wpe(pos)  # position embeddings of shape (t, n_embd)
        x = self.transformer.drop(tok_emb + pos_emb)
        attention_mask = model_inputs.attention_mask.bool()
        attention_mask = attention_mask[:, None, None, :]

        for block in self.transformer.h:
            x = block(x, attention_mask=attention_mask)
        if self.is_causal:
            lengths = model_inputs.attention_mask.sum(-1)
            last_timestep = lengths - 1
            emb = x[torch.arange(x.shape[0]), last_timestep]
        else:
            outputmask = (model_inputs.input_ids != self.pad_token_id).unsqueeze(-1).float()
            emb = (x * outputmask).sum(1) / outputmask.sum(1)
        return emb


if __name__ == "__main__":
    # mdl = GPT2TextEncoder(model_name='openai-community/gpt2-xl')
    mdl = ScratchTextEncoder(is_causal=True)
    q = mdl(["Hello where are you ?", "And here?"], "cpu")
    print(q.shape)
