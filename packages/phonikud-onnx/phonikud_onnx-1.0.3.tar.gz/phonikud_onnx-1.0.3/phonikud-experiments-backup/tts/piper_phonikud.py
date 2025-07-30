"""
wget https://www.openslr.org/resources/134/saspeech_gold_standard_v1.0.tar.gz
tar xf saspeech_gold_standard_v1.0.tar.gz

wget https://huggingface.co/thewh1teagle/phonikud-onnx/resolve/main/phonikud-1.0.int8.onnx -O phonikud-1.0.int8.onnx
wget https://huggingface.co/thewh1teagle/phonikud-tts-checkpoints/resolve/main/model.onnx -O tts-model.onnx
wget https://huggingface.co/thewh1teagle/phonikud-tts-checkpoints/resolve/main/model.config.json -O tts-model.config.json

uv sync
uv run saspeech_piper.py
"""

from pathlib import Path
import soundfile as sf
from tqdm import tqdm
from phonikud_tts import Phonikud, phonemize, Piper
import json
import time
import re



with open('metadata_non_vocalized_map.json') as fp:
    MAP = json.load(fp)
    
def phonemize_by_map(text: str) -> str:
    phonemes = []
    for i in text:
        if i in MAP:
            phonemes.append(MAP[i])
        else:
            phonemes.append(i)
    return ''.join(phonemes)

def get_sentences_dict() -> dict[str, str]:
    with open('saspeech_seed0_sentences.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    phonikud = Phonikud('phonikud-1.0.int8.onnx')
    piper = Piper('export_non_vocalized.onnx', 'tts-model.config.json')
    output_dir = Path('./non_wav_vocalized')
    output_dir.mkdir(parents=True, exist_ok=True) # uv run src/tts_transcribe_errors.py --mode wer --ref_path ./../tts/saspeech_seed0_sentences.json --transcripts_path ./transcribed_vocalized.json   --report_path report_vocalized.json

    sentences_dict = get_sentences_dict()

    for k, text in tqdm(sorted(sentences_dict.items(), key=lambda item: int(item[0])), desc="Generating speech", unit="utterance"):
        if len(text.split()) < 6:
            # make 2x longer sentence from it as it contains too few words
            text = ' '.join([text] * 2)
            print(f'Warning: Sentence {k} is too short, repeating it to make it longer.', f'New text: {text}')
            
        # text = "שלום וברכה ניפרד בשמחה ממומין"
        # text = "בַּתְּמוּנָה הַגְּדוֹלָה עָמְדוּ אָדָם, אִשְׁתּוֹ סִיוָן, וְהַבַּת הַגְּדוֹלָה שֶׁלָּהֶם אַלְמוֹג."
        # text = "בתמונה הגדולה עמדו אדם, אשתו סיון, והבת הגדולה שלהם אלמוג."
        start_t = time.time()
        # with_diacritics = phonikud.add_diacritics(text)
        end_t = time.time()
        # print(f"Added with phonikud in {end_t - start_t:.2f} seconds")
        start_t = time.time()
        # with_diacritics = with_diacritics.replace('|', '').replace('\u05ab', '').replace('\u05bd', '')
        text = re.sub('[\u05b0-\u05c7]', '', text) # remove all diacritics
        phonemes =  phonemize_by_map(text) #phonemize(with_diacritics) # phonemize(with_diacritics)
        # breakpoint()
        end_t = time.time()
        # print(f"Phonemized with phonikud in {end_t - start_t:.2f} seconds")
        # remove stress
        # phonemes = phonemes.replace('ˈ', '')
        start_t = time.time()
        samples, sample_rate = piper.create(phonemes, is_phonemes=True)
        end_t = time.time()
        # RTF
        time_took = end_t - start_t
        audio_duration = len(samples) / sample_rate
        rtf = time_took / audio_duration if audio_duration > 0 else float('inf')
        # print(f"Generated {k} in {time_took:.2f} seconds, audio duration: {audio_duration:.2f} seconds, RTF: {rtf:.2f}")
        out_path = output_dir / f"{k}.wav"
        sf.write(out_path, samples, sample_rate, subtype="PCM_16")


if __name__ == "__main__":
    main()
