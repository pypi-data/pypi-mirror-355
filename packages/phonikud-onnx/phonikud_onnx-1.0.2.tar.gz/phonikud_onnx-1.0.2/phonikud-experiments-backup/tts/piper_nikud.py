"""
wget https://www.openslr.org/resources/134/saspeech_gold_standard_v1.0.tar.gz
tar xf saspeech_gold_standard_v1.0.tar.gz

wget https://huggingface.co/thewh1teagle/phonikud-onnx/resolve/main/phonikud-1.0.int8.onnx -O phonikud-1.0.int8.onnx
wget https://huggingface.co/thewh1teagle/phonikud-tts-checkpoints/resolve/main/model.onnx -O tts-model.onnx
wget https://huggingface.co/thewh1teagle/phonikud-tts-checkpoints/resolve/main/model.config.json -O tts-model.config.json

wget https://huggingface.co/thewh1teagle/phonikud-tts-checkpoints/resolve/main/auto_phonemize_exp/metadata_nikud_map.json

uv sync
uv run saspeech_piper.py
"""

from pathlib import Path
import soundfile as sf
from tqdm import tqdm
from phonikud_tts import Phonikud, Piper
from dicta_onnx import Dicta
import json
import time


with open('metadata_nikud_map.json', 'r', encoding='utf-8') as fp:
    metadata_nikud_map = json.load(fp)

def phonemize(text: str) -> str:
    phonemes = ''
    for i in text:
        phonemes += metadata_nikud_map.get(i, i)
    return phonemes
    

def get_sentences_dict() -> dict[str, str]:
    with open('saspeech_seed0_sentences.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    dicta = Dicta('dicta-1.0.onnx')
    piper = Piper('nikud.onnx', 'tts-model.config.json')
    output_dir = Path('./nikud_tts_wav')
    output_dir.mkdir(parents=True, exist_ok=True)

    sentences_dict = get_sentences_dict()

    for k, text in tqdm(sorted(sentences_dict.items(), key=lambda item: int(item[0])), desc="Generating speech", unit="utterance"):
        if len(text.split()) < 6:
            # make 2x longer sentence from it as it contains too few words
            text = ' '.join([text] * 2)
            print(f'Warning: Sentence {k} is too short, repeating it to make it longer.', f'New text: {text}')
        
        # text = "פתוח, רוח, תפוח, ריח, קרח, פורח, זורח"
        # text = "איזה תפוח טעים! הרוח כזו חזקה! תוכנה בקוד פתוח! איזה ריח טוב! הוא ממש פורח! הוא ממש זורח!"
        text = "שלום וברכה ניפרד בשמחה ממומין"
        start_t = time.time()
        with_diacritics = dicta.add_diacritics(text)
        end_t = time.time()
        print(f"Added with dicta in {end_t - start_t:.2f} seconds")
        phonemes = phonemize(with_diacritics)
        
        # remove stress
        # phonemes = phonemes.replace('ˈ', '')
        start_t = time.time()
        samples, sample_rate = piper.create(phonemes, is_phonemes=True)
        end_t = time.time()
        # RTF
        time_took = end_t - start_t
        audio_duration = len(samples) / sample_rate
        rtf = time_took / audio_duration if audio_duration > 0 else float('inf')
        print(f"Generated {k} in {time_took:.2f} seconds, audio duration: {audio_duration:.2f} seconds, RTF: {rtf:.2f}")
        out_path = output_dir / f"{k}.wav"
        sf.write(out_path, samples, sample_rate, subtype="PCM_16")


if __name__ == "__main__":
    main()
