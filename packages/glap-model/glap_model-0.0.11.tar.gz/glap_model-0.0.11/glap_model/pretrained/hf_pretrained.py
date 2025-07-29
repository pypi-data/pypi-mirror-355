from typing import (
    Any,
    Dict,
)
from ..models import (
    GLAP,
)

from transformers import (
    PreTrainedModel,
    PretrainedConfig,
)
# from huggingface_hub import PyTorchModelHubMixin


class GLAPConfig(PretrainedConfig):
    model_type = "glap"  # Unique identifier for AutoConfig

    def __init__(
        self,
        embed_size: int = 1024,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.embed_size = embed_size
        self.audio_encoder_args: Dict[
            str,
            Any,
        ] = dict(pretrained=False)  # We load the GLAP checkpoint, not the pretrained Dasheng


class GLAPPretrainedModel(PreTrainedModel):
    config_class = GLAPConfig

    def __init__(
        self,
        config,
    ):
        super().__init__(config)
        self.model_impl = GLAP(
            audio_encoder_args=dict(),
            embed_size=config.embed_size,
        )


if __name__ == "__main__":
    import torch

    mdl = GLAPPretrainedModel(GLAPConfig())
    print(mdl)
    mdl.model_impl.from_pretrained("https://zenodo.org/records/15493136/files/glap_checkpoint.pt?download=1")
    # cfg = GLAPConfig()
    mdl.save_pretrained("mymodel/")
