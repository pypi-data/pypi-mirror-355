"""
wget https://huggingface.co/thewh1teagle/phonikud-tts-checkpoints/resolve/main/auto_phonemize_exp/metadata_nikud.csv
"""

from phonikud_onnx import Phonikud
import phonikud
from tqdm import tqdm
model = Phonikud('phonikud-1.0.int8.onnx')

with open('metadata_plain.csv', 'r') as fp:
    lines = fp.readlines()
data = {k:v for k, v in (line.strip().split('|') for line in lines)}


new_data = []
with open('metadata_non_enhanced.csv', 'w') as fp:
    for k, v in tqdm(data.items()):
        with_diacritics = model.add_diacritics(v)
        with_diacritics = with_diacritics.replace('|', '').replace('\u05ab', '').replace('\u05bd', '')
        phonemes = phonikud.phonemize(with_diacritics)
        new_data.append([k, phonemes])
    data = '\n'.join(['|'.join(item) for item in new_data])
    fp.write(data)