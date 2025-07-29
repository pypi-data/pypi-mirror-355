from phonemizers import phonikud_phonemizer
import jiwer

with open('metadata.csv') as fp:
    lines = fp.readlines()
    data = {k:v for k, v in (line.strip().split('|') for line in lines if line.strip())}

print(data)