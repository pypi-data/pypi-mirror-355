import random
import json
import re
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Generate 100 random samples from a metadata file.")
    parser.add_argument("input_path", type=str, help="Path to the input CSV file.")
    parser.add_argument("output_path", type=str, help="Path to the output JSON file.")
    return parser.parse_args()

args = parse_args()
input_path = args.input_path
output_path = args.output_path
seed = 0

# Regex pattern to remove Hebrew nikud (Unicode range 0x05B0 to 0x05C7)
nikud_pattern = re.compile(r'[\u05B0-\u05C7]')

# Read all lines and extract only the third field (text)
with open(input_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

texts = []
for line in lines:
    parts = line.strip().split('|')
    if len(parts) == 3:
        # Remove nikud from the text
        clean_text = nikud_pattern.sub('', parts[2])
        texts.append(clean_text)

# Set seed for reproducibility
random.seed(seed)

# Pick 100 random texts (or fewer if less than 100 lines)
sampled_texts = random.sample(texts, min(100, len(texts)))

# Create dictionary with string keys
data = {str(i): text for i, text in enumerate(sampled_texts)}

# Write JSON output
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
