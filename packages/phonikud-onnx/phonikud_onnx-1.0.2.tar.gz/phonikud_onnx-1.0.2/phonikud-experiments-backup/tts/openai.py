"""
# https://platform.openai.com/api-keys
export OPENAI_API_KEY="key"
"""
import os
import json
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "https://api.openai.com/v1/audio/speech"

def get_sentences_dict() -> dict[str, str]:
    with open('generate_100_random.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

os.makedirs('./openai', exist_ok=True)

sentences = get_sentences_dict()

for key, sentence in sentences.items():
    payload = {
        "model": "gpt-4o-mini-tts",
        "voice": "coral",
        "input": sentence,
        "instructions": (
            "Voice: Clear, authoritative, and composed, projecting confidence and professionalism.\n\n"
            "Tone: Neutral and informative, maintaining a balance between formality and approachability.\n\n"
            "Punctuation: Structured with commas and pauses for clarity, ensuring information is digestible and well-paced.\n\n"
            "Delivery: Steady and measured, with slight emphasis on key figures and deadlines to highlight critical points."
        ),
        "response_format": "wav"
    }

    response = requests.post(API_URL, headers=headers, json=payload, stream=True)

    if response.ok:
        file_path = f'./openai/{key}.wav'
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)
        print(f"Saved audio for key '{key}' to {file_path}")
    else:
        print(f"Error for key '{key}': {response.status_code}")
        print(response.text)
