"""
uv sync
uv run mms.py ../metrics/data/text_hand.json ../mms_wav
"""

from transformers import VitsModel, AutoTokenizer
import torch
import time
import numpy as np

text = "שלום וברכה ניפרד בשמחה ממומין"

model = VitsModel.from_pretrained("facebook/mms-tts-heb")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-heb")

inputs = tokenizer(text, return_tensors="pt")

durations = []
gen_times = []


for _ in range(10):
    start = time.time()
    with torch.no_grad():
        output = model(**inputs).waveform
    end = time.time()

    wav = output.squeeze().cpu().numpy()
    duration = len(wav) / model.config.sampling_rate
    print(f'Generated audio duration: {duration:.2f} seconds in {end - start:.2f} seconds')

    durations.append(duration)
    gen_times.append(end - start)

mean_duration = np.mean(durations)
mean_gen_time = np.mean(gen_times)
print(f'Mean audio duration: {mean_duration:.2f} seconds')
print(f'Mean generation time: {mean_gen_time:.2f} seconds')
