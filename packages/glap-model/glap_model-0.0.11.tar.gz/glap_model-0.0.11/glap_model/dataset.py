from __future__ import annotations
from loguru import logger
import warnings
from functools import partial
from pathlib import Path
from ignite.handlers.tqdm_logger import ProgressBar
import torch
import torch.utils.data
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple, Union
import numpy as np
import webdataset as wds
import random
import re
import tempfile


def fast_warn_and_continue(exn):
    warnings.warn(repr(exn))
    return True


# Same as wds, but added useless extension check for opus
def decode_torch_audio(key, data):
    """Decode audio using the torchaudio library.

    :param key: file name extension
    :param data: data to be decoded
    """

    extension = re.sub(r".*[.]", "", key)
    if extension not in ["flac", "mp3", "sox", "wav", "m4a", "ogg", "wma", "opus"]:
        return None

    import torchaudio
    import os

    with tempfile.TemporaryDirectory() as dirname:
        fname = os.path.join(dirname, f"file.{extension}")
        with open(fname, "wb") as stream:
            stream.write(data)
        return torchaudio.load(fname)


def exists(x) -> bool:
    return x is not None


def db_to_linear(scalar: float) -> float:
    return 10 ** (scalar / 20)


def argsort_py(seq: Sequence):
    return sorted(range(len(seq)), key=seq.__getitem__)


def generate_ngrams(input_list: List[int], ngram: int = 3) -> List[List[int]]:
    output = []
    for i in range(len(input_list) - ngram + 1):
        output.append(input_list[i : i + ngram])
    return output


def _sort_by_length(
    data, bufsize=1000, initial=100, length_index: int = 0, dim: int = -1, reverse: bool = False, handler=None
):
    """Shuffle the data in the stream.

    This uses a buffer of size `bufsize`. Shuffling at
    startup is less random; this is traded off against
    yielding samples quickly.

    data: iterator
    bufsize: buffer size for shuffling
    length_index: int The index where to find the length to sort
    returns: iterator
    rng: either random module or random.Random instance

    """
    buf = []
    for sample in data:
        buf.append(sample)
        if len(buf) < bufsize:
            try:
                next_data = next(data)
                buf.append(next_data)  # skipcq: PYL-R1708
            except StopIteration:
                pass
    while len(buf) > 0:
        buf.sort(key=lambda item: item[length_index].shape[dim])
        for batch in buf:
            yield batch
        buf = []


sort_by_length = wds.pipelinefilter(_sort_by_length)


def _seq_crop_captions(
    data,
    max_audio_length: Optional[float] = None,
    mono: bool = True,
    drop_clipped: bool = True,
    random_gain: Tuple[int, int] | None = None,
    handler=None,
):
    """WebDataset crop filter, yields (audio,caption) pairs"""
    for sample in data:
        audio, captions, *extra = sample
        audio, sr = audio
        if mono and audio.ndim == 2:
            audio = audio.mean(0)
        if audio.abs().max() >= 0.99 and drop_clipped:
            continue

        if random_gain is not None:
            factor = db_to_linear(np.random.uniform(*random_gain))
            audio *= factor

        for caption in captions:
            # caption = text_preprocess(caption)
            # Use different crops for each caption
            if exists(max_audio_length):
                max_audio_length_samples = int(max_audio_length * sr)
                if audio.shape[-1] > max_audio_length_samples:
                    start = random.randint(0, audio.shape[-1] - max_audio_length_samples)
                    audio = audio[start : start + max_audio_length_samples]
            yield (audio, caption, *extra)


class Audiowebdataset(wds.DataPipeline):
    def __init__(
        self,
        urls,
        tar_shuffle: Optional[int] = None,
        resample: bool = False,
        target_sample_rate: int = 16000,
        batch_size: int = 1,
        filter_function: Optional[Callable] = None,
        rename_keys: Dict[str, str] = dict(audio="flac;mp3;sox;wav;m4a;ogg;wma", text="json;jsonl", filename="__key__"),
        map_kwargs: Optional[Dict[str, Callable]] = None,
        merge_function: Optional[
            Callable
        ] = None,  # merge function is called before batching. In the merge function we can operate on the data in form of a tuple
        handler=fast_warn_and_continue,
    ):
        from functools import partial

        self.urls = urls
        pipeline: List = [wds.ResampledShards(urls) if resample else wds.SimpleShardList(urls)]
        if tar_shuffle is not None:
            # Tar wise shuffle
            pipeline.extend(
                [
                    wds.detshuffle(
                        bufsize=tar_shuffle,
                        initial=tar_shuffle // 4,
                    ),
                    wds.split_by_node,
                    wds.split_by_worker,
                    # at this point, we have an iterator over the shards assigned to each worker at each node
                    wds.tarfile_to_samples(handler=handler),
                    wds.shuffle(
                        bufsize=tar_shuffle,
                        initial=tar_shuffle // 4,
                    ),
                ]
            )
        else:
            pipeline.extend([wds.split_by_worker, wds.tarfile_to_samples(handler=handler)])
        # Decode i.e., bytes object to a python-accessible obj.
        pipeline.extend([wds.decode(decode_torch_audio, handler=handler), wds.rename(**rename_keys, handler=handler)])

        if map_kwargs:
            pipeline.extend([wds.map_dict(**map_kwargs)])
        # Filter function takes a sample (key: value) as input and returns True for valid samples, otherwise false
        if filter_function:
            pipeline.extend([wds.select(filter_function)])

        # Resample audio, useful when dataset is not monotonous in sampling rate
        if target_sample_rate:
            import torchaudio

            assert "audio" in rename_keys.keys(), "target_sample_rate requires key_maps=dict(audio='flac;mp3;wav')"

            def resample_audio(audio_sr: Tuple[torch.Tensor, int]) -> Tuple[torch.Tensor, int]:
                audio, sr = audio_sr
                audio = torchaudio.functional.resample(audio, sr, target_sample_rate)
                return (audio, target_sample_rate)

            pipeline.extend([wds.map_dict(audio=resample_audio)])

        # Webdataset support batching and parallel reading using
        # num_workers only with tuples, not dicts
        pipeline.extend(
            [
                wds.to_tuple(*rename_keys.keys()),
            ]
        )
        if merge_function is not None:
            pipeline.extend([merge_function])

        # Batch but do not merge into tensors yet
        pipeline.append(
            wds.batched(
                batch_size,
                collation_fn=partial(wds.filters.default_collation_fn, combine_tensors=False, combine_scalars=False),
                partial=True,
            ),
        )
        super().__init__(pipeline)


class BalancedDatasetSampler(wds.DataPipeline, wds.compat.FluidInterface):
    def __init__(self, datasets: Dict[str, Audiowebdataset], probs=None):
        super().__init__()
        self.datasets = datasets
        if probs is None:
            probs = [1.0] * len(self.datasets)
        self.probs = probs

    def __iter__(self):
        sources = {k: iter(ds) for k, ds in self.datasets.items()}
        while True:
            for k, source in random.choices(list(sources.items()), weights=self.probs):
                try:
                    yield next(source)
                except StopIteration:
                    break


def expand_with_brace(lists: List[str]):
    import braceexpand

    r = []
    for a_list in lists:
        if "*" in a_list:
            # Expand using "posix" based *
            a_list = braceexpand.braceexpand(a_list)
            for expand_l in a_list:
                r.extend(map(str, Path(expand_l).parent.glob(Path(expand_l).name)))
        else:
            r.extend(braceexpand.braceexpand(a_list))
    logger.debug(f"Found {len(r)} number of .tars")
    return r


def pad(tensorlist: Sequence[torch.Tensor], padding_value: float = 0.0):
    # Tensors are expected to be B, ..., T
    lengths = [f.shape[-1] for f in tensorlist]
    dims = tensorlist[0].shape
    trailing_dims = dims[:-1]
    batch_dim = len(lengths)
    num_raw_samples = max(lengths)
    out_dims = (batch_dim,) + trailing_dims + (num_raw_samples,)
    out_tensor = torch.full(out_dims, fill_value=padding_value, dtype=tensorlist[0].dtype)
    for i, tensor in enumerate(tensorlist):
        length = tensor.shape[-1]
        out_tensor[i, ..., :length] = tensor[..., :length]
    return out_tensor, torch.as_tensor(lengths)


def collate_with_lengths_wds(samples, combine_scalars=True, combine_tensors=True):
    batched = list(zip(*samples))
    result = []
    for idx, b in enumerate(batched):
        if isinstance(b[0], (int, float)):
            if combine_scalars:
                b = np.array(list(b))
        elif isinstance(b[0], torch.Tensor):
            if combine_tensors:
                b = pad(list(b))
        elif isinstance(b[0], np.ndarray):
            if combine_tensors:
                b = np.array(list(b))
        else:
            b = list(b)
        result.append(b)
    return result


def create_webdataset(
    urls: Union[List[str], Dict[str, List[str]]],
    tar_shuffle: Optional[int] = None,
    resample: Optional[bool] = None,
    num_workers: int = 4,
    drop_clipped: bool = False,
    batch_size: int = 1,
    sample_rate: int = 16000,
    training: bool = False,  # Do shuffle or?
    cross_worker_shuffle: int = 512,  # Only when training = True
    random_gain: Optional[Tuple[int, int]] = None,  # Adds random gain
    sample_weights: List[float] | None = None,
    min_audio_length: float | None = None,
    max_audio_length: float | None = None,
    max_text_length: int | None = None,
    multilingual_prob: float = 0.1,
    mix_languages: Literal[
        "all", "zho_Hans", "deu_Latn", "cat_Latn", "spa_Latn", "jpn_Jpan", "fra_Latn", "nld_Latn"
    ] = "all",
    sample_by_length: int | None = None,
):
    # We filter max_audio_length in the merge function
    # Idea is that we get different samples (crops) for one text
    def filter_lengths(sample):
        audio, sr = sample["audio"]
        text = sample["text"]
        if isinstance(text, str):
            text_length = len(text)
        else:
            text_length = max(len(t) for t in text)  # packed list[]
        audio_length = audio.shape[-1] / sr
        if exists(min_audio_length) and audio_length < min_audio_length:
            return False
        if exists(max_text_length) and text_length > max_text_length:
            return False
        return True

    # Check if a translation is abnormal i.e., repeats, or length
    def check_abnormal_string(astring: str) -> bool:
        ngrams = generate_ngrams(list(astring.encode("utf-8")), 4)
        ngram_count_max = np.unique(ngrams, axis=0, return_counts=True)[-1].max()
        is_invalid = ngram_count_max > 4
        if not is_invalid:
            if exists(max_text_length) and (len(astring) > max_text_length):
                return True
        return is_invalid

    def text_from_json(sample_at_it):
        for key in ["captions", "caption", "text"]:
            parsed_text_sample = sample_at_it.get(key, None)
            if parsed_text_sample is not None:
                # We assume that there are multiple captions per audio sample
                if isinstance(parsed_text_sample, str):
                    parsed_text_sample = [parsed_text_sample]
                parsed_text_sample = parsed_text_sample.copy()
                # During training, we want to mix with other translations
                if training:
                    # keys that we save are in format key_target_lang i.e.,:
                    # captions_de_Latn
                    keys_in_sample = list(sample_at_it.keys())

                    def select_lang(lang_str) -> bool:
                        if mix_languages == "all":
                            return lang_str.startswith(
                                f"{key}_"
                            )  # The multilingual data is formatted as caption_deu_Latn
                        else:
                            return mix_languages in lang_str

                    multilingual_captions_idxs = np.where([select_lang(sample_key) for sample_key in keys_in_sample])[0]
                    has_multilingual_captions = len(multilingual_captions_idxs) > 0
                    if has_multilingual_captions:
                        # If we pass i.e., 8 captions, a probability of 10% would lead to 80% more samples. Avoid that using by scaling with number of captions
                        scaled_multilingual_prob = multilingual_prob / len(multilingual_captions_idxs)
                        for multi_lang_idx in multilingual_captions_idxs:
                            # Randomly just pick one of the samples, only really effective for clotho ..., zhiyong style
                            selected_sample = random.choice(sample_at_it[keys_in_sample[multi_lang_idx]])
                            if random.random() < scaled_multilingual_prob:
                                if not check_abnormal_string(selected_sample):
                                    parsed_text_sample.append(selected_sample)
                return parsed_text_sample

    dataset_kwargs = dict(
        tar_shuffle=tar_shuffle,
        target_sample_rate=sample_rate,
        resample=resample,
        batch_size=batch_size,
        filter_function=filter_lengths,
        rename_keys=dict(
            audio="flac;mp3;sox;wav;m4a;ogg;wma;opus",
            text="json",
            filename="__key__",
        ),
        map_kwargs=dict(text=lambda json_data: text_from_json(json_data)),
        merge_function=partial(
            _seq_crop_captions,
            drop_clipped=drop_clipped,
            random_gain=random_gain,
            mono=True,
            max_audio_length=max_audio_length,
        ),
    )

    if isinstance(urls, dict):
        ds = {k: Audiowebdataset(expand_with_brace(train_data), **dataset_kwargs) for k, train_data in urls.items()}
        dataset = BalancedDatasetSampler(datasets=ds, probs=sample_weights)
    else:
        dataset = Audiowebdataset(expand_with_brace(urls), **dataset_kwargs)

    dataloader = wds.WebLoader(
        dataset,
        batch_size=None,
        pin_memory=True,
        num_workers=num_workers,
        persistent_workers=(num_workers > 0) and training,
    ).unbatched()
    if training:
        dataloader = dataloader.shuffle(cross_worker_shuffle)
        if sample_by_length:
            dataloader = dataloader.compose(sort_by_length(bufsize=sample_by_length, initial=128))

    dataloader = dataloader.batched(
        batch_size, collation_fn=collate_with_lengths_wds, partial=not training
    )  # During training remove last batch
    return dataloader


def create_zeroshot_eval_webdataset(
    urls: Union[List[str], Dict[str, List[str]]],
    sample_rate: int = 16000,
    batch_size: int = 32,
    num_workers: int = 4,
):
    def extract_label_from_json(json_dict):
        for k in ["label", "labels"]:
            if k in json_dict:
                target = json_dict[k]
                if isinstance(target, str):
                    # Tolist to avoid using padding in length_wds
                    target = np.array(target.split(";"), dtype=int).tolist()
                return target

    def _merge_function(data, mono=True):
        for sample in data:
            (audio, sr), *extra = sample
            if mono and audio.ndim == 2:
                audio = audio.mean(0)
            # Remove samplerate at sample[0]
            yield (audio, *extra)

    dataset_kwargs = dict(
        tar_shuffle=False,
        target_sample_rate=sample_rate,
        resample=False,
        batch_size=batch_size,
        rename_keys=dict(
            audio="flac;mp3;sox;wav;m4a;ogg;wma;opus",
            label="json",
            filename="__key__",
        ),
        map_kwargs=dict(label=lambda json_data: extract_label_from_json(json_data)),
        merge_function=_merge_function,
    )
    dataset = Audiowebdataset(expand_with_brace(urls), **dataset_kwargs)
    dataloader = wds.WebLoader(
        dataset,
        batch_size=None,
        pin_memory=True,
        num_workers=num_workers,
    ).unbatched()
    dataloader = dataloader.batched(batch_size, collation_fn=collate_with_lengths_wds, partial=True)
    return dataloader
