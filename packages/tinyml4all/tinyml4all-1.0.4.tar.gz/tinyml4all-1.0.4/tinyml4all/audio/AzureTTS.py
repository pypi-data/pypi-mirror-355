import os.path
import shelve
from pathlib import Path
from typing import List, cast

from azure.cognitiveservices.speech import (
    SpeechConfig,
    SpeechSynthesisOutputFormat,
    SpeechSynthesizer,
    VoiceInfo,
)
from azure.cognitiveservices.speech.audio import AudioOutputConfig

from tinyml4all.audio.WAV import WAV
from tinyml4all.support import assert_folder


class AzureTTS:
    """
    Generate speech from text
    """

    def __init__(self, api_key: str, region: str):
        """

        :param api_key:
        :param region:
        """
        self.api_key = api_key
        self.region = region

    @property
    def sdk(self) -> SpeechConfig:
        """
        Get instance of SDK
        :return:
        """
        return SpeechConfig(subscription=self.api_key, region=self.region)

    def get_voices(self, language: str) -> List[str]:
        """
        Get list of supported voices for language
        :param language:
        :return:
        """
        with shelve.open("azure") as cache:
            voices = cache.get("voices")

            if voices is None:
                sdk = self.sdk
                synthesizer = SpeechSynthesizer(sdk, None)
                voices = [
                    voice.short_name
                    for voice in synthesizer.get_voices_async(language).get().voices
                ]
                cache["voices"] = voices

        return voices

    def synthesize(
        self,
        text: str,
        duration: str,
        save_to: str,
        voice: str = "en-US-AvaMultilingualNeural",
        pitch: int = 0,
        rate: int = 0,
        freq: int = 16_000,
    ):
        """
        Synthesize speech
        :param freq:
        :param rate:
        :param duration:
        :param save_to:
        :param pitch:
        :param text:
        :param voice:
        :return:
        """
        assert_folder(os.path.abspath(os.path.dirname(save_to)))
        assert -100 <= pitch <= 100, "pitch must be between -100 and 100"

        lang = voice[:5]
        prosody = {}

        if pitch != 0:
            pitch_sign = "+" if pitch > 0 else "-"
            prosody["pitch"] = f"{pitch_sign}{pitch}%"

        if rate != 0:
            prosody["rate"] = f"{rate}%"

        if len(prosody) > 0:
            attributes = " ".join(f'{key}="{value}"' for key, value in prosody.items())
            text = f"<prosody {attributes}>{text}</prosody>"

        pause = 10 if rate < 0 else 100

        ssml = f"""
            <speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="{lang}">
                <voice name="{voice}">
                    <break time="{pause}ms" />
                    {text}
                </voice>
            </speak>
        """

        speech_config = self.sdk
        speech_config.set_speech_synthesis_output_format(
            SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
        )
        audio_config = AudioOutputConfig(filename=save_to)
        speech_config.speech_synthesis_voice_name = voice
        synthesizer = SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )
        synthesizer.speak_ssml(ssml)

        if os.stat(save_to).st_size == 0:
            os.unlink(save_to)
            print(
                "Generation failed with params",
                {"text": text, "lang": lang, "prosody": prosody},
            )
            raise AssertionError("No speech generated")

        # force frequency and duration
        WAV(path=save_to).resample(freq).trim(duration).write()

        return True
