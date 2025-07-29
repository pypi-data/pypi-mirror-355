import torch.distributed as dist
from accelerate import Accelerator, DistributedDataParallelKwargs

from glap_model import models
from glap_model.models import losses
from glap_model.models.losses import LossProxy, LossProxyDDP, LossProxySingleNode
from glap_model.config import GlapTrainConfig
from typing import Any, Dict, List, Optional
import torch
from glap_model.grad_cache.functional import cached


def gather_tensors(t, dim=0):
    gathered = [torch.empty_like(t) for _ in range(dist.get_world_size())]
    dist.all_gather(gathered, t)
    gathered[dist.get_rank()] = t
    return torch.cat(gathered, dim=dim)


# For GradCache
@cached
def call_model(model, input):
    return model(**input)


# This class is esp. useful for ddp
class CLAPTrainer(torch.nn.Module):
    def __init__(
        self, config: GlapTrainConfig, accelerator: Optional[Accelerator] = None, prepare_model: bool = True
    ) -> None:
        super().__init__()

        self.model = getattr(models, config.model)(**config.model_args)
        if "8bit" in config.optimizer:
            import bitsandbytes as bnb

            optimizer_template = getattr(bnb.optim, config.optimizer)
        else:
            optimizer_template = getattr(torch.optim, config.optimizer)

        ddp_kwargs = DistributedDataParallelKwargs(find_unused_parameters=True)
        self.accelerator = accelerator if accelerator is not None else Accelerator(kwargs_handlers=[ddp_kwargs])
        self.use_ddp_loss = config.use_ddp_loss
        self.use_grad_cache = config.grad_cache > 1

        loss_func = getattr(losses, config.loss)(
            temperature=config.temperature, embed_regularization=config.embed_regularization, **config.loss_args
        )

        loss_wrapper = LossProxy
        if self.use_ddp_loss or self.use_grad_cache:
            if self.accelerator.num_processes == 1:
                loss_wrapper = LossProxySingleNode
            else:
                # Merges batches across each gpu for DDP training
                loss_wrapper = LossProxyDDP
        self.loss_func = loss_wrapper(loss_func)
        self.optimizer = optimizer_template(
            list(self.model.parameters()) + list(self.loss_func.parameters()), **config.optimizer_args
        )
        self.grad_cache_size = config.grad_cache
        if self.use_grad_cache:
            self.audio_cache, self.text_cache, self.closure_cache = [], [], []
            self.loss_cache = torch.tensor(10.0)

        if prepare_model:
            self._prepare_accelerate()

    def _prepare_accelerate(self):
        self.model, self.loss_func, self.optimizer = self.accelerator.prepare(
            self.model, self.loss_func, self.optimizer
        )

    @classmethod
    def from_checkpoint(cls, checkpoint: str, config: GlapTrainConfig, accelerator: Accelerator | None = None):
        dump = torch.load(checkpoint, map_location="cpu")
        model_parameters = dump["model"]
        inst = cls(config, accelerator=accelerator, prepare_model=False)
        inst.model.load_state_dict(model_parameters)
        inst._prepare_accelerate()
        return inst

    def state_dict(self, *args, **kw):
        return self.accelerator.unwrap_model(self.model).state_dict(*args, **kw)

    def _optimizer(self):
        return self.accelerator.unwrap_model(self.optimizer)

    def forward(
        self,
        model_inputs: Dict[str, Any],
        return_loss=True,
        filenames: List[str] | None = None,  # unique ids for each sample, used to
    ):
        #  Note that Text is a List[str], and will be convereted to embs in sonar/text encoder
        model_inputs = {
            k: v.to(self.accelerator.device) if isinstance(v, torch.Tensor) else v for k, v in model_inputs.items()
        }
        with self.accelerator.accumulate(self.model):
            # Single worker
            if not self.use_ddp_loss and not self.use_grad_cache:
                loss_or_embds = self.model(**model_inputs)
                if return_loss:
                    loss_or_embds = self.loss_func(*loss_or_embds, filenames=filenames)
                    self.accelerator.backward(loss_or_embds)
                    if self.accelerator.sync_gradients:
                        self.accelerator.clip_grad_norm_(self.model.parameters(), 1.0)
                    self.optimizer.step()
                    self.optimizer.zero_grad()
                return loss_or_embds
            if self.use_ddp_loss and self.accelerator.state.num_processes > 1:
                audio_embeddings, text_embeddings = self.model(**model_inputs)
                if return_loss:
                    loss = self.loss_func(
                        audio_embeddings,
                        text_embeddings,
                    )
                    self.accelerator.backward(loss)
                    if self.accelerator.sync_gradients:
                        self.accelerator.clip_grad_norm_(self.model.parameters(), 1.0)
                    self.optimizer.step()
                    self.optimizer.zero_grad()
                    return loss
                return audio_embeddings, text_embeddings
            elif self.use_grad_cache:
                audio_embed, text_embed, rep_model = call_model(self.model, model_inputs)
                if return_loss:
                    self.audio_cache.append(audio_embed)
                    self.text_cache.append(text_embed)
                    self.closure_cache.append(rep_model)
                    # Only used to display a reasonable loss
                    loss = self.loss_cache
                    if len(self.audio_cache) == self.grad_cache_size:
                        self.optimizer.zero_grad()
                        loss = self.loss_func(
                            self.audio_cache,
                            self.text_cache,
                        )
                        self.accelerator.backward(loss)
                        for f, a, t in zip(self.closure_cache, self.audio_cache, self.text_cache):
                            f((a, t))
                        if self.accelerator.sync_gradients:
                            self.accelerator.clip_grad_norm_(self.model.parameters(), 1.0)
                        self.optimizer.step()
                        self.optimizer.zero_grad()
                        self.audio_cache, self.text_cache, self.closure_cache, self.filename_cache = [], [], [], []
                        self.loss_cache = loss
                    return loss
                return audio_embed, text_embed
