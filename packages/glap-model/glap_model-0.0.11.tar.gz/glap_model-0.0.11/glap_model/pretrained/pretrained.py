from ..models import GLAP
from ..models import GLAPInference


PRETRAINED_CHECKPOINTS = {
    "glap": "https://zenodo.org/records/15493136/files/glap_checkpoint.pt?download=1",
}


def glap_train(pretrained: bool = True, **model_kwargs) -> GLAP:
    if pretrained:
        return GLAP.from_pretrained(PRETRAINED_CHECKPOINTS["glap"], **model_kwargs)
    return GLAP()


def glap_inference(**model_kwargs) -> GLAPInference:
    return GLAPInference.from_pretrained(PRETRAINED_CHECKPOINTS["glap"], **model_kwargs)
