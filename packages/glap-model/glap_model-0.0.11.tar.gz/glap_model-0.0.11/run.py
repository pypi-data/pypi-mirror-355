#!/usr/bin/env python3
from __future__ import annotations
import contextlib
from pathlib import Path
from itertools import islice
from fire import Fire
from accelerate import Accelerator
from ignite.metrics.accuracy import Accuracy
from ignite.metrics.epoch_metric import EpochMetric
from loguru import logger
from typing import Iterable, List, Literal, Union
import torch
import pandas as pd

import ignite
from ignite.engine import Events, Engine
from ignite.handlers.tqdm_logger import ProgressBar
from ignite.handlers import (
    Checkpoint,
    DiskSaver,
    global_step_from_engine,
    CosineAnnealingScheduler,
    EarlyStopping,
    LRScheduler,
    create_lr_scheduler_with_warmup,
)
from glap_model.config import GlapTrainConfig, GlapEvalConfig, GlapZeroshotConfig
from glap_model.dataset import create_webdataset, create_zeroshot_eval_webdataset
from glap_model import models
from glap_model.metrics import CLAPScore
from glap_model.trainer import CLAPTrainer


def batched(iterable, n, *, strict=False):
    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        if strict and len(batch) != n:
            raise ValueError("batched(): incomplete batch")
        yield batch


class Runner(object):
    def __init__(self, seed: int = 42, nthreads: int = 1) -> None:
        super().__init__()
        ignite.utils.manual_seed(seed)
        torch.set_num_threads(nthreads)
        logger.info(f"Using seed {seed}")

    def __create_dir_and_log(self, config_parameters: GlapTrainConfig):
        config_parameters.outputpath.mkdir(exist_ok=True, parents=True)
        logger.add(
            config_parameters.outputpath / config_parameters.logfile,
            enqueue=True,
            level="INFO",
            format="[{level} {time:YYYY-MM-DD HH:mm:ss}] {message}",
        )
        for k, v in config_parameters.to_dict().items():
            logger.info(f"{k}: {v}")

    def train(self, config, **overwrite_kwargs):
        config_parameters = GlapTrainConfig.parse_config_or_kwargs(config, **overwrite_kwargs)
        from accelerate.utils import DistributedDataParallelKwargs

        kwargs = DistributedDataParallelKwargs(find_unused_parameters=True)

        accelerator = Accelerator(
            gradient_accumulation_steps=config_parameters.accumulate_num, kwargs_handlers=[kwargs]
        )
        if accelerator.is_main_process:
            self.__create_dir_and_log(config_parameters)

        if config_parameters.pretrained is not None:
            logger.info(f"Loading pretrained model {config_parameters.pretrained}")
            model = CLAPTrainer.from_checkpoint(
                str(config_parameters.pretrained),
                config=config_parameters,
                accelerator=accelerator,
            )
        else:
            model = CLAPTrainer(config_parameters, accelerator=accelerator)

        train_dataloader = create_webdataset(
            config_parameters.train_data,
            tar_shuffle=config_parameters.tar_shuffle,
            resample=config_parameters.resample,
            num_workers=config_parameters.num_workers,
            drop_clipped=config_parameters.drop_clipped,
            batch_size=config_parameters.batch_size,
            random_gain=config_parameters.random_gain,
            sample_rate=config_parameters.sample_rate,
            sample_weights=config_parameters.balanced_sampler,
            max_audio_length=config_parameters.max_audio_length,
            max_text_length=config_parameters.max_text_length,
            min_audio_length=config_parameters.min_audio_length,
            mix_languages=config_parameters.mix_languages,
            multilingual_prob=config_parameters.multilingual_prob,
            sample_by_length=config_parameters.sample_by_length,
            training=True,
        )

        eval_dataloaders = {
            k: create_webdataset(
                v,
                num_workers=config_parameters.num_workers,
                batch_size=config_parameters.eval_batch_size,  # Assert batch_size = 1 during testing to avoid padding for now
                sample_rate=config_parameters.sample_rate,
                training=False,
            )
            for k, v in config_parameters.test_data.items()
        }

        if config_parameters.epoch_length and config_parameters.epoch_length > 0:
            max_steps = int(config_parameters.epoch_length * config_parameters.epochs)
            scheduler = CosineAnnealingScheduler(
                model.optimizer,
                "lr",
                model.optimizer.param_groups[0]["lr"],
                model.optimizer.param_groups[0]["lr"] * config_parameters.decay_frac,
                max_steps,
            )
        else:
            # A dummy for create_lr_scheduler_with_warmup
            scheduler = LRScheduler(torch.optim.lr_scheduler.LambdaLR(model.optimizer, lr_lambda=[lambda epoch: 1.0]))
        warmup_num = config_parameters.warmup_iters
        warmup_epochs_num = config_parameters.warmup_epochs
        if warmup_epochs_num is not None and warmup_epochs_num > 0 and config_parameters.epoch_length:
            warmup_num = int(warmup_epochs_num * config_parameters.epoch_length)

        if warmup_num is not None and warmup_num > 0:
            scheduler = create_lr_scheduler_with_warmup(scheduler, warmup_start_value=0.0, warmup_duration=warmup_num)

        @torch.enable_grad()
        def train_batch(engine, batch):
            model.train()
            with accelerator.accumulate(model):
                (audio, audio_length), text, filename = batch
                # Use the filename counts as weights, i.e., if a fn is seen twice, half the loss for each
                model_inputs = dict(audio=audio, audio_length=audio_length, text=text)
                # We do all the logic within the model
                loss = model(model_inputs, filenames=filename, return_loss=True)

                return {
                    "total_loss": loss.item(),
                    "lr": model._optimizer().param_groups[0]["lr"],
                }

        @torch.inference_mode()
        def inference_batch(engine, batch):
            model.eval()
            with accelerator.autocast():
                (audio, audio_length), text, unique_audio_id = batch
                model_inputs = dict(audio=audio, audio_length=audio_length, text=text)
                audio_embeds, text_embeds = model(model_inputs, return_loss=False)
            return audio_embeds, text_embeds

        train_engine = Engine(train_batch)
        inference_engine = Engine(inference_batch)
        ProgressBar(bar_format=None, disable=not accelerator.is_main_process).attach(
            train_engine, output_transform=lambda x: x
        )
        ProgressBar(bar_format=None, disable=not accelerator.is_main_process).attach(inference_engine)
        CLAPScore(num_caps=config_parameters.eval_num_caps).attach(inference_engine, "clapscore")

        ignite.metrics.RunningAverage(alpha=0.99, output_transform=lambda x: x["total_loss"]).attach(
            train_engine, "avg_loss"
        )

        def log_metric_results(engine, title=""):
            if accelerator.is_main_process:
                results = engine.state.metrics
                output_str_list = [f"{title:<10} Results - Epoch : {train_engine.state.epoch:<4}"]
                for metric in results:
                    metric_values = results[metric]
                    metric_result_list = []
                    if isinstance(metric_values, dict):
                        metric_result_list += [f"{metric:<10} : "]
                        for k, v in metric_values.items():
                            metric_result_list += [f"{k:<10} : {v:<4.4f}"]
                    else:
                        output_str_list += [f"{metric} {results[metric]:<5.4f}"]
                output_str_list += [f"LR : {model.optimizer.param_groups[0]['lr']:.2e}"]
                logger.info(" ".join(output_str_list))

        train_engine.add_event_handler(Events.EPOCH_COMPLETED, log_metric_results, "Train")
        train_engine.add_event_handler(Events.ITERATION_COMPLETED, ignite.handlers.terminate_on_nan.TerminateOnNan())
        train_engine.add_event_handler(Events.ITERATION_STARTED, scheduler)

        target_metrics = [("mAP10", 1.0), ("r1", 1.0)]

        # Checkpoints for each metric/dataset
        checkpoint_savers = {}
        for test_name in eval_dataloaders.keys():
            for metric, coef in target_metrics:
                checkpoint_savers[test_name + metric] = Checkpoint(
                    {
                        "model": model,
                        "config": config_parameters,
                    },
                    DiskSaver(config_parameters.outputpath),
                    n_saved=config_parameters.n_saved,
                    filename_prefix=f"best_{metric}_{test_name}",
                    score_function=Checkpoint.get_default_score_fn(metric, coef),
                    global_step_transform=global_step_from_engine(train_engine),
                )
        inference_engine.add_event_handler(
            Events.COMPLETED,
            Checkpoint(
                {
                    "model": model,
                    "config": config_parameters,
                },
                DiskSaver(config_parameters.outputpath),
                n_saved=config_parameters.n_saved,
                global_step_transform=global_step_from_engine(train_engine),
            ),
        )

        def run_inference(train_engine, add_label: str = ""):
            for test_name, test_dataloader in eval_dataloaders.items():
                with contextlib.ExitStack() as stack:
                    stack.enter_context(
                        inference_engine.add_event_handler(
                            Events.COMPLETED, log_metric_results, f"{add_label}{test_name}"
                        )
                    )
                    for metric, coef in target_metrics:
                        stack.enter_context(
                            inference_engine.add_event_handler(Events.COMPLETED, checkpoint_savers[test_name + metric])
                        )
                    inference_engine.run(test_dataloader)

        if config_parameters.early_stop is not None:
            earlystop_handler = EarlyStopping(
                patience=config_parameters.early_stop,
                score_function=Checkpoint.get_default_score_fn(*target_metrics[0]),
                trainer=train_engine,
            )
            inference_engine.add_event_handler(Events.COMPLETED, earlystop_handler)
        train_engine.add_event_handler(
            Events.EPOCH_COMPLETED(every=config_parameters.valid_every) | Events.COMPLETED, run_inference
        )

        scheduler = accelerator.prepare(scheduler)

        train_engine.run(
            train_dataloader, max_epochs=config_parameters.epochs, epoch_length=config_parameters.epoch_length
        )
        accelerator.wait_for_everyone()
        if accelerator.is_main_process:
            # for checkpoint_savers
            for k, v in checkpoint_savers.items():
                self.evaluate(v.last_checkpoint)

    def evaluate(
        self,
        experiment_path: str | Path,
        data: Literal[
            "all",
            "clotho_caps",
            "ljspeech",
            "librispeech",
            "acd",
            "gigaspeech",
            "aishell",
            "musiccaps",
            "vctk",
            "songdescriber",
        ] = "all",
    ):
        logger.info(f"Running eval for data {data} and checkpoint {experiment_path}")
        experiment_path = Path(experiment_path)
        if experiment_path.is_file():  # Best model passed!
            checkpoint = str(experiment_path)
            experiment_path = experiment_path.parent  # Just set upper path as default
        else:
            checkpoint = next(Path(f"{experiment_path}").glob("*check*"))
        model = models.GLAPInference.from_pretrained(str(checkpoint))
        checkpoint_name = Path(checkpoint).stem
        logger.add(
            experiment_path / f"eval_{checkpoint_name}.txt",
            enqueue=True,
            level="INFO",
            format="[<red>{level}</red> <green>{time:YYYY-MM-DD HH:mm:ss}</green>] {message}",
        )
        config = model.config
        eval_configs: List[GlapEvalConfig] = []
        if data == "clotho_caps" or data == "all":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="e_val_data_clotho",
                        data_path=["data/Clotho/val/val_000000.tar.gz"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=5,
                    ),
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="e_val_data_ac",
                        data_path=["data/AudioCaps/val/val_000000.tar.gz"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=5,
                    ),
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="test_data_ac",
                        data_path=["data/AudioCaps/test/test_000000.tar.gz"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=5,
                    ),
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="test_data_clotho",
                        data_path=["data/Clotho/test/test_000000.tar.gz"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=5,
                    ),
                ]
            )
        if data == "acd" or data == "all":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="test_acd",
                        data_path=["./data/ACD/test_acd/test_acd_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                ]
            )
        if data == "librispeech" or data == "all":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="test_librispeech_clean",
                        data_path=["./data/LibriSpeech/test/test_clean/test_clean_wav_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="test_librispeech_other",
                        data_path=["./data/LibriSpeech/test/test_other/test_other_wav_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                ]
            )
        if data == "gigaspeech" or data == "all":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="dev_gigaspeech",
                        data_path=["./data/GigaSpeech/dev/gigaspeech_dev_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="test_gigaspeech",
                        data_path=["./data/GigaSpeech/test/gigaspeech_test_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                ]
            )
        if data == "aishell" or data == "all":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="test_aishell",
                        data_path=["./data/AISHELL2/test_aishell_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                ]
            )
        if data == "musiccaps" or data == "all":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="musicaps_eval",
                        data_path=["./data/MusicCaps/musiccaps/musiccaps_eval_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                ]
            )
        if data == "songdescriber" or data == "all":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="songdescriber_valid",
                        data_path=["./data/Songdescriber/valid_song_describer_single_cap_0000000.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                ]
            )
        if data == "vctk":
            eval_configs.extend(
                [
                    GlapEvalConfig(
                        experiment_path=experiment_path,
                        data_name="vctk",
                        data_path=["./data/VCTK/train_44k_with_text_00000{00..08}.tar"],
                        sample_rate=config.sample_rate,
                        num_workers=config.num_workers,
                        num_caps=1,
                    ),
                ]
            )

        all_results = []
        for eval_config in eval_configs:
            result_df = self._run_evaluate(eval_config=eval_config, model=model, return_df=True)
            assert result_df is not None
            result_df["checkpoint"] = checkpoint_name
            all_results.append(result_df)

        all_results = pd.concat(all_results)
        all_results.to_csv(
            experiment_path / f"result_all_{checkpoint_name}.tsv", sep="\t", float_format="%.2f", index=True
        )
        logger.info("\n" + all_results.to_markdown())

    def _run_evaluate(
        self,
        eval_config: GlapEvalConfig,
        model: torch.nn.Module,
        return_df: bool = False,
    ):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        eval_dataloader = create_webdataset(
            eval_config.data_path,
            num_workers=eval_config.num_workers,
            batch_size=eval_config.batch_size,  # Assert batch_size = 1 during testing to avoid padding for now
            min_audio_length=0.3,  # In gigaspeech there are samples of 140ms
            sample_rate=eval_config.sample_rate,
            training=False,
        )

        def inference_batch(engine, batch):
            model.eval()
            with torch.inference_mode():
                (audio, audio_length), text, unique_audio_id = batch
                model_inputs = dict(audio=audio, audio_length=audio_length)

                model_inputs = {k: v.to(device) for k, v in model_inputs.items()}
                # Text is still a list
                model_inputs["text"] = text
                with torch.autocast(device_type=str(device)):
                    audio_embeds, text_embeds = model(**model_inputs, return_loss=False)
            return audio_embeds, text_embeds

        inference_engine = Engine(inference_batch)
        ProgressBar().attach(inference_engine)

        # A2T and T2A
        CLAPScore(num_caps=eval_config.num_caps, average=False).attach(inference_engine, "scores")

        output_tsv = eval_config.experiment_path / f"results_{eval_config.data_name}.tsv"
        # remove old result.tsv
        Path(output_tsv).unlink(missing_ok=True)

        result_df = []

        def log_metric_results(engine, title=""):
            df = pd.DataFrame(engine.state.metrics, index=[title])[
                ["t2a_r1", "t2a_r5", "t2a_r10", "t2a_mAP10", "a2t_r1", "a2t_r5", "a2t_r10", "a2t_mAP10"]
            ]
            result_df.append(df)
            results = engine.state.metrics
            output_str_list = [f"{title:<10} Results"]
            for metric in results:
                metric_values = results[metric]
                metric_result_list = []
                if isinstance(metric_values, dict):
                    metric_result_list += [f"{metric:<10} : "]
                    for k, v in metric_values.items():
                        metric_result_list += [f"{k:<10} : {v:<4.4f}"]
                else:
                    output_str_list += [f"{metric} {results[metric]:<5.4f}"]
            logger.info("\n".join(output_str_list))

        with inference_engine.add_event_handler(Events.EPOCH_COMPLETED, log_metric_results, f"{eval_config.data_name}"):
            inference_engine.run(eval_dataloader)
        if return_df:
            return pd.concat(result_df)
        else:
            logger.info(f"Result file at {output_tsv}")
            result_df = pd.concat(result_df)
            result_df.to_csv(output_tsv, mode="w", sep="\t", float_format="%.2f", index=True)

    # Simple zeroshot inference for a model + text
    def zeroshot(
        self,
        experiment_path: Union[str, Path],
        audio_path: str,
        text: str,  # Should be split for multiple sentences using ;
    ):
        import torchaudio

        experiment_path = Path(experiment_path)
        if experiment_path.is_file():  # Best model passed!
            checkpoint = str(experiment_path)
            experiment_path = experiment_path.parent  # Just set upper path as default
        else:
            checkpoint = next(Path(f"{experiment_path}").glob("*check*"))
        model = models.GLAPInference.from_pretrained(str(checkpoint))
        accelerator = Accelerator()
        model = model.to(accelerator.device)
        audio, sr = torchaudio.load(audio_path)
        if sr != 16000:
            audio = torchaudio.functional.resample(audio, sr, 16000)
        if audio.shape[0] > 1:
            audio = audio.mean(0, keepdim=True)

        audio_length = torch.tensor(audio.shape[-1]).unsqueeze(0)

        def clapscore(audio_emb, text_emb):
            return (100 * (audio_emb @ text_emb.T)).squeeze(0)

        model.eval()
        texts = text.split(";")
        with torch.inference_mode():
            model_inputs = dict(audio=audio, audio_length=audio_length)

            model_inputs = {k: v.to(accelerator.device) for k, v in model_inputs.items()}
            # Text is still a list
            model_inputs["text"] = texts
            with accelerator.autocast():
                audio_embeds, text_embeds = model(**model_inputs, return_loss=False)
            scores = clapscore(audio_embeds, text_embeds)
        for score, text in zip(scores, texts):
            logger.info(f"{text} : {score:.2f}")

    def eval_zeroshot(
        self,
        config: str | Path,
        experiment_path: str | Path,
        **kwargs,
    ):
        config_parameters = GlapZeroshotConfig.parse_config_or_kwargs(
            config_file=config, experiment_path=experiment_path, **kwargs
        )
        model = models.GLAPInference.from_pretrained(str(config_parameters.checkpoint))
        accelerator = Accelerator()
        model = model.to(accelerator.device)
        model = model.eval()
        # Prefix to all queries
        prefix = config_parameters.prefix  # Prefix for each text
        postfix = config_parameters.postfix  # Prefix for each text
        label_maps = config_parameters.label_maps  # Mappings from int -> text
        # Maps idx -> text such that ids match
        labels_as_text = [f"{prefix}{label_maps[lab]}{postfix}" for lab in sorted(label_maps)]

        # Fixed for the evaluation
        with torch.inference_mode():
            text_embeds = []
            for text_batch in batched(labels_as_text, 16):
                text_embeds.append(model.forward_text(text_batch, device=accelerator.device))
            text_embeds = torch.cat(text_embeds, dim=0)

        def score_embeds(audio_emb, text_emb):
            ret = audio_emb @ text_emb.T
            return ret

        def generate_multihot_label(label_lst: List[int]):
            multi_target = torch.zeros(len(label_lst), len(label_maps))
            for i, sample in enumerate(label_lst):
                multi_target[i].scatter_(0, torch.tensor(sample), 1)
            return multi_target

        @torch.inference_mode()
        def inference_batch(engine, batch):
            model.eval()
            with accelerator.autocast():
                (audio, audio_length), target, unique_audio_id = batch
                # Only forward the audio, since text stays constant
                audio_embeds = model(
                    audio.to(accelerator.device),
                    audio_length=audio_length.to(accelerator.device),
                )
            return audio_embeds, text_embeds, target

        average_statistics = []

        def log_metric_results(engine, title=""):
            df = pd.DataFrame(engine.state.metrics, index=[title])
            average_statistics.append(df)

            results = engine.state.metrics
            output_str_list = [f"{title:<10} Results"]
            for metric in results:
                metric_values = results[metric]
                metric_result_list = []
                if isinstance(metric_values, dict):
                    metric_result_list += [f"{metric:<10} : "]
                    for k, v in metric_values.items():
                        metric_result_list += [f"{k:<10} : {v:<4.4f}"]
                else:
                    output_str_list += [f"{metric} {results[metric]:<5.4f}"]
            logger.info("\n".join(output_str_list))

        used_metrics = set()
        # Go over all provided datasets in form of a name + urls (tars)
        for name, urls in config_parameters.data_path.items():
            inference_engine = Engine(inference_batch)
            ProgressBar().attach(inference_engine)
            inference_engine.add_event_handler(Events.COMPLETED, log_metric_results, f"{name}")
            dataloader = create_zeroshot_eval_webdataset(
                urls, batch_size=config_parameters.batch_size, num_workers=config_parameters.num_workers
            )
            # Get first target of the dataloader, check if its a list, its multi-label -> no accuracy
            _, target, *_ = next(iter(dataloader))
            if isinstance(target, list):
                from sklearn.metrics import average_precision_score

                def average_precision_score_compute_fn(y_pred, y_true):
                    return average_precision_score(y_true, y_pred, average="macro")

                (
                    EpochMetric(
                        compute_fn=average_precision_score_compute_fn,
                        check_compute_fn=False,
                        output_transform=lambda output: (
                            score_embeds(*output[:2]).cpu(),
                            generate_multihot_label(output[-1]).cpu(),
                        ),
                    )
                    * 100
                ).attach(inference_engine, "mAP")
                used_metrics.add("mAP")
            else:
                (
                    Accuracy(
                        output_transform=lambda output: (
                            score_embeds(*output[:2]).cpu(),
                            torch.as_tensor(output[-1]).cpu(),
                        )
                    )
                    * 100
                ).attach(inference_engine, "accuracy")
                used_metrics.add("accuracy")
            inference_engine.run(dataloader)
        # These are accumulated during runs
        if len(average_statistics) > 0:
            df = pd.concat(average_statistics).reset_index().rename(columns={"index": "task"})
            df["prefix"] = prefix
            df["postfix"] = postfix
            zeroshot_taskwise_filename = (
                Path(config_parameters.experiment_path) / f"results_zeroshot_taskwise_{Path(config).stem}.tsv"
            )
            zeroshot_avg_filename = (
                Path(config_parameters.experiment_path) / f"results_zeroshot_average_{Path(config).stem}.tsv"
            )
            df.to_csv(zeroshot_taskwise_filename, sep="\t", index=False)
            logger.info(df)
            pattern = "([^_]+)"  # Everything before _
            df["task_avg"] = df["task"].str.extract(pattern, expand=False)
            avg_df = df.groupby("task_avg")[list(used_metrics)].mean().reset_index()
            avg_df.to_csv(zeroshot_avg_filename, sep="\t", float_format="%.2f", index=False)
            logger.info(f"Output at {zeroshot_avg_filename}")
            logger.info(avg_df)

    def translate_sonar(
        self,
        *data: List[str],
        output_path: Path = Path("data/translations"),
        source_lang="eng_Latn",
        replace: bool = False,
        target_lang: Iterable[
            Literal[
                "ita_Latn",
                "mar_Deva",
                "tur_Latn",
                "khk_Cyrl",
                "uig_Arab",
                "azj_Latn",
                "tel_Telu",
                "dyu_Latn",
                "kor_Hang",
                "tgk_Cyrl",
                "taq_Latn",
                "taq_Tfng",
                "cat_Latn",
                "acm_Arab",
                "khm_Khmr",
                "ltz_Latn",
                "cjk_Latn",
                "ell_Grek",
                "spa_Latn",
                "knc_Latn",
                "nya_Latn",
                "sag_Latn",
                "mag_Deva",
                "wol_Latn",
                "kam_Latn",
                "kmr_Latn",
                "aka_Latn",
                "ben_Beng",
                "bod_Tibt",
                "fij_Latn",
                "ars_Arab",
                "lug_Latn",
                "ary_Arab",
                "swh_Latn",
                "ind_Latn",
                "slk_Latn",
                "tum_Latn",
                "dik_Latn",
                "san_Deva",
                "gaz_Latn",
                "twi_Latn",
                "azb_Arab",
                "lao_Laoo",
                "hau_Latn",
                "bho_Deva",
                "kaz_Cyrl",
                "mni_Beng",
                "gle_Latn",
                "pan_Guru",
                "kab_Latn",
                "war_Latn",
                "pag_Latn",
                "bak_Cyrl",
                "tgl_Latn",
                "eng_Latn",
                "fra_Latn",
                "jav_Latn",
                "deu_Latn",
                "vec_Latn",
                "ace_Arab",
                "est_Latn",
                "lvs_Latn",
                "epo_Latn",
                "sna_Latn",
                "shn_Mymr",
                "crh_Latn",
                "mya_Mymr",
                "lua_Latn",
                "por_Latn",
                "kik_Latn",
                "quy_Latn",
                "bos_Latn",
                "grn_Latn",
                "apc_Arab",
                "tir_Ethi",
                "umb_Latn",
                "zho_Hant",
                "lin_Latn",
                "mal_Mlym",
                "fao_Latn",
                "arb_Arab",
                "ayr_Latn",
                "ewe_Latn",
                "ajp_Arab",
                "isl_Latn",
                "kas_Arab",
                "zul_Latn",
                "lus_Latn",
                "mri_Latn",
                "fuv_Latn",
                "xho_Latn",
                "slv_Latn",
                "nob_Latn",
                "ilo_Latn",
                "lij_Latn",
                "lmo_Latn",
                "dzo_Tibt",
                "tpi_Latn",
                "ukr_Cyrl",
                "ban_Latn",
                "kir_Cyrl",
                "plt_Latn",
                "run_Latn",
                "nno_Latn",
                "kin_Latn",
                "ace_Latn",
                "bjn_Arab",
                "jpn_Jpan",
                "kbp_Latn",
                "hye_Armn",
                "glg_Latn",
                "sin_Sinh",
                "som_Latn",
                "bul_Cyrl",
                "ltg_Latn",
                "snd_Arab",
                "hin_Deva",
                "ron_Latn",
                "yue_Hant",
                "ydd_Hebr",
                "yor_Latn",
                "cym_Latn",
                "hrv_Latn",
                "kan_Knda",
                "nus_Latn",
                "heb_Hebr",
                "pap_Latn",
                "bam_Latn",
                "asm_Beng",
                "ces_Latn",
                "lit_Latn",
                "tsn_Latn",
                "zho_Hans",
                "kea_Latn",
                "mai_Deva",
                "ssw_Latn",
                "sun_Latn",
                "bem_Latn",
                "amh_Ethi",
                "kac_Latn",
                "vie_Latn",
                "mos_Latn",
                "srd_Latn",
                "gla_Latn",
                "fon_Latn",
                "awa_Deva",
                "urd_Arab",
                "afr_Latn",
                "bug_Latn",
                "sat_Beng",
                "zsm_Latn",
                "tam_Taml",
                "aeb_Arab",
                "tso_Latn",
                "eus_Latn",
                "nld_Latn",
                "sot_Latn",
                "kat_Geor",
                "kmb_Latn",
                "kon_Latn",
                "ibo_Latn",
                "hun_Latn",
                "nso_Latn",
                "tha_Thai",
                "srp_Cyrl",
                "ast_Latn",
                "lim_Latn",
                "uzn_Latn",
                "mkd_Cyrl",
                "kas_Deva",
                "dan_Latn",
                "bjn_Latn",
                "min_Latn",
                "rus_Cyrl",
                "smo_Latn",
                "tuk_Latn",
                "ckb_Arab",
                "fin_Latn",
                "ory_Orya",
                "hne_Deva",
                "swe_Latn",
                "pbt_Arab",
                "mlt_Latn",
                "acq_Arab",
                "luo_Latn",
                "hat_Latn",
                "tzm_Tfng",
                "guj_Gujr",
                "scn_Latn",
                "npi_Deva",
                "prs_Arab",
                "tat_Cyrl",
                "fur_Latn",
                "oci_Latn",
                "ceb_Latn",
                "knc_Arab",
                "szl_Latn",
                "pol_Latn",
                "bel_Cyrl",
                "pes_Arab",
                "als_Latn",
                "arz_Arab",
            ]
        ] = [
            "zho_Hans",
            "deu_Latn",
            "cat_Latn",
            "spa_Latn",
            "jpn_Jpan",
            "fra_Latn",
            "nld_Latn",
        ],
    ):
        import webdataset as wds
        from tqdm import tqdm
        import json
        from sonar.inference_pipelines.text import TextToTextModelPipeline

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        accelerator = Accelerator(mixed_precision="fp16")
        text2text = TextToTextModelPipeline(
            encoder="text_sonar_basic_encoder",
            decoder="text_sonar_basic_decoder",
            tokenizer="text_sonar_basic_encoder",
            device=accelerator.device,
        )

        def text_from_json(sample):
            for key in ["caption", "captions", "text"]:
                r = sample.get(key, None)
                # We assume that there are multiple captions per audio sample
                if isinstance(r, str):
                    r = [r]
                if r is not None:
                    return key, r

        target_lang = [target_lang] if isinstance(target_lang, str) else target_lang

        # split_by_node for ddp support
        dataset = wds.DataPipeline(
            wds.SimpleShardList(data),
            wds.split_by_node,  # each card gets individual .tar
            wds.tarfile_to_samples(),
            wds.decode(),
        )
        sinks = {}

        with torch.inference_mode():
            for item in tqdm(dataset, disable=not accelerator.is_main_process):
                text_key, text = text_from_json(item.pop("json"))
                fname = Path(item["__url__"]).name
                sink = sinks.get(fname, None)
                if sink is None:
                    sink = wds.TarWriter(
                        f"{output_path / fname}",
                        encoder=False,
                        compress="tar.gz" in fname,
                    )
                    sinks[fname] = sink

                json_data = {text_key: text}
                with accelerator.autocast():
                    for tar_lang in target_lang:
                        translated_sentences = text2text.predict(text, source_lang=source_lang, target_lang=tar_lang)
                        if replace:
                            text_key = f"{text_key}"
                        else:
                            text_key = f"{text_key}_{tar_lang}"
                        json_data[text_key] = translated_sentences

                json_data = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
                to_write = {**item, "json": json_data}
                sink.write(to_write)
        for _, sink in sinks.items():
            sink.close()


if __name__ == "__main__":
    Fire(Runner)
