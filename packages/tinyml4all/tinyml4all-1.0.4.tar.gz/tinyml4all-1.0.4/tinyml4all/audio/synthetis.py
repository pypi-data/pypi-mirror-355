import concurrent.futures
import logging
import os.path
import random
from itertools import product
from typing import List, Union

import joblib
from tqdm import tqdm

from tinyml4all.audio.AzureTTS import AzureTTS

from tinyml4all.audio.support import parse_freq
from tinyml4all.support import cast, assert_folder
from tinyml4all.support.types import coalesce


def synthesize_speech(
    api_key: str,
    region: str,
    text: Union[str, List[str]],
    language: str,
    duration: str,
    save_to: str,
    num_samples: int,
    freq: str = "16 khz",
    pitches: List[int] = None,
    rates: List[int] = None,
):
    """
    Synthesize words using Azure TTS
    :param api_key:
    :param region:
    :param text:
    :param language:
    :param duration:
    :param save_to:
    :param num_samples:
    :param freq:
    :param pitches:
    :param rates:
    :return:
    """
    assert num_samples > 0, "num_samples must be greater than 0"
    assert_folder(os.path.abspath(save_to))

    azure = AzureTTS(api_key, region)
    voices = azure.get_voices(language)

    text = cast(text, List, lambda text: [text])
    pitches = coalesce(pitches, [0, -15, 15])
    rates = coalesce(rates, [0, -0])
    combinations = list(product(text, voices, pitches, rates))
    combinations = random.sample(combinations, num_samples)

    arguments = [
        {
            "text": txt,
            "duration": duration,
            "save_to": os.path.join(save_to, f"{txt}_{voice}_p{pitch}_r{rate}.wav"),
            "voice": voice,
            "pitch": pitch,
            "rate": rate,
            "freq": parse_freq(freq),
        }
        for txt, voice, pitch, rate in combinations
    ]

    # run synthesis in parallel
    with concurrent.futures.ThreadPoolExecutor() as pool:

        def synthesize(**kwargs):
            try:
                return azure.synthesize(**kwargs)
            except AssertionError:
                logging.error(f"Can't synthesize speech with params {kwargs}")

        pool = joblib.Parallel(n_jobs=-1)
        results = list(
            tqdm(
                pool(joblib.delayed(synthesize)(**kwargs) for kwargs in arguments),
                total=len(arguments),
            )
        )
        valid_results = [res for res in results if res is not None]
        print(f"Generated {len(valid_results)} synthetic samples")
