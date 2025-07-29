from __future__ import annotations
from dataclasses import dataclass, field, asdict
import datetime
import yaml
from pathlib import Path
import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from loguru import logger
import sys

# Make the logger with this format the default for all loggers in this package
logger.configure(
    handlers=[
        {
            "sink": sys.stderr,
            "format": "<fg #FF6900>(GLAP)</fg #FF6900> [<green>{time:YYYY-MM-DD HH:mm:ss}</green>] {message}",
            "level": "DEBUG",
        }
    ]
)


@dataclass
class GlapTrainConfig:
    train_data: Union[Dict, List[Union[str, Path]]]
    test_data: Dict[str, List[Union[str, Path]]]
    outputpath: Path = Path("experiments/glap/")
    pretrained: Optional[Path] = None
    logfile: str = "train.log"
    config_file: str = ""

    ## Data
    accumulate_num: int = 1
    sample_rate: int = 16000
    num_workers: int = 4
    warmup_iters: Optional[int] = 1000
    warmup_epochs: Optional[int] = None
    epochs: int = 500
    epoch_length: int = 10000
    optimizer: str = "AdamW8bit"
    optimizer_args: Dict = field(default_factory=lambda: {"lr": 0.0001, "betas": [0.8, 0.9]})
    random_gain: Optional[Tuple[int, int]] = None
    resample: bool = True
    drop_clipped: bool = True
    balanced_sampler: None | List[float] = None
    initial_upsample_factor: int = 1  # Upsample the inputs before feeding into Vocoder
    tar_shuffle: int = 64
    drop_below_db: Optional[float] = 0  # Drop crops with less energy than 0 db, i.e,, silence
    decay_frac: float = 0.1
    early_stop: int = 50
    max_audio_length: Optional[float] = None  # maximal audio length
    min_audio_length: Optional[float] = None  # minimal audio length
    max_text_length: Optional[int] = None  # maximal number of text tokens
    cross_worker_shuffle: int = 512
    valid_every: int = 1
    mix_languages: Literal[
        "all", "zho_Hans", "deu_Latn", "cat_Latn", "spa_Latn", "jpn_Jpan", "fra_Latn", "nld_Latn"
    ] = "all"  # For multilingal training only, select the language
    multilingual_prob: float = 0.1  # For multilingal training only
    sample_by_length: int | None = (
        None  # Sampling buffer size if one wants to sample by length. Length refers to audio length
    )

    ## Model
    model: str = "GLAP"
    model_args: Dict[str, Any] = field(
        default_factory=lambda: dict(
            audio_encoder="DashengWrapper",
            audio_encoder_args=dict(pretrained=True),
            text_encoder="sonar",
            text_encoder_args={},
            embed_size=1024,
        )
    )
    embed_regularization: bool = True
    temperature: float = 0.07  # Loss Temperator
    use_ddp_loss: bool = False  # Loss across all devices
    grad_cache: int = 1
    loss: str = "AudioTextContrastiveLoss"
    loss_args: Dict[str, Any] = field(default_factory=lambda: dict())

    batch_size: int = 64
    eval_batch_size: int = 1  # Default batch_size
    n_saved: int = 1
    eval_num_caps: int = 5

    def __post_init__(self):
        self.outputpath = (
            Path(self.outputpath)
            / Path(self.config_file).stem
            / f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}_{uuid.uuid1().hex}"
        )

    def to_dict(self):
        return asdict(self)

    def state_dict(self):
        return self.to_dict()

    @classmethod
    def load_state_dict(cls, state):
        return cls(**state)

    @classmethod
    def parse_config_or_kwargs(cls, config_file: Union[Path, str], **overwrite_kwargs):
        with open(config_file) as con_read:
            yaml_config = yaml.load(con_read, Loader=yaml.FullLoader)
        # values from config file are all possible params
        arguments = cls(**dict(yaml_config, config_file=config_file, **overwrite_kwargs))
        return arguments


@dataclass
class GlapEvalConfig:
    data_name: str
    data_path: List[str]
    experiment_path: Path
    batch_size: int = 1
    sample_rate: int = 16000
    num_workers: int = 2
    num_caps: int = 1

    def __post_init__(self):
        # Get nearest multiple of num_caps
        if self.batch_size % self.num_caps != 0:
            self.batch_size = self.batch_size + self.num_caps - (self.batch_size % self.num_caps)


@dataclass
class GlapZeroshotConfig:
    experiment_path: str | Path | None
    data_path: Dict[str, List[str]]
    prefix: str = ""
    postfix: str = ""
    sample_rate: int = 16000
    num_workers: int = 4
    batch_size: int = 64
    config_file: str | None = None
    label_map_file: Path | str | None = None

    def __post_init__(self):
        if self.experiment_path is not None:
            self.experiment_path = Path(self.experiment_path)
            checkpoint = None
            if self.experiment_path.is_file():  # Best model passed!
                checkpoint = str(self.experiment_path)
                self.experiment_path = self.experiment_path.parent  # Just set upper path as default
            elif self.experiment_path.is_dir():
                checkpoint = next(Path(f"{self.experiment_path}").glob("*check*"))
            self.checkpoint = checkpoint
        import pandas as pd

        self.label_maps = pd.read_csv(self.label_map_file, sep="\t").set_index("idx")["name"].to_dict()

    @classmethod
    def parse_config_or_kwargs(cls, config_file: Union[Path, str], **overwrite_kwargs):
        with open(config_file) as con_read:
            yaml_config = yaml.load(con_read, Loader=yaml.FullLoader)
        # values from config file are all possible params
        arguments = cls(**dict(yaml_config, config_file=config_file, **overwrite_kwargs))
        return arguments
