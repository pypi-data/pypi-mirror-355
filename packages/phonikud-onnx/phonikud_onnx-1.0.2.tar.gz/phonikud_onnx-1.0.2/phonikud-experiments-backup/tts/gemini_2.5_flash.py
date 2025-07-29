"""
# https://aistudio.google.com/apikey
export GEMINI_API_KEY="key"
"""
import os
import requests
import json
import base64
import soundfile as sf
from pathlib import Path
from tqdm import tqdm
import numpy as np

def get_sentences_dict() -> dict[str, str]:
    with open('generate_100_random.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = "gemini-2.5-flash-preview-tts"
GENERATE_CONTENT_API = "streamGenerateContent"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:{GENERATE_CONTENT_API}?key={GEMINI_API_KEY}"
HEADERS = {"Content-Type": "application/json"}

output_dir = Path("gemini_output")
output_dir.mkdir(exist_ok=True)

sentences = get_sentences_dict()

for key, sentence in tqdm(sentences.items(), desc="Generating audio"):
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": sentence
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["audio"],
            "temperature": 1,
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Zephyr"
                    }
                }
            }
        }
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    if response.ok:
        data = response.json()
        try:
            audio_b64 = data[0]["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            audio_bytes = base64.b64decode(audio_b64)

            # Convert bytes to numpy int16 array (16-bit PCM)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

            wav_path = output_dir / f"{key}.wav"
            sf.write(wav_path, audio_np, samplerate=24000, subtype='PCM_16')

        except (KeyError, IndexError) as e:
            print(f"\nError parsing audio for '{key}': {e}")

    else:
        print(f"\nError for '{key}': {response.status_code}")
        print(response.text)
