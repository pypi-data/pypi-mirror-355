"""
uv sync
uv run src/phonemize_wer.py --phonemize
uv run src/phonemize_wer.py --evaluate
"""

import argparse
import json
from pathlib import Path
from jiwer import cer, wer
from tqdm import tqdm

# from phonemizers import charisiu, phonikud_phonemizer, espeak, goruut, nakdimon_phonikud, dicta_phonikud, dicta_naive, nakdimon_naive, phonikud_naive
from phonemizers import phonikud_phonemizer

phonemizers = {
    "phonikud": phonikud_phonemizer.phonemize,
    # "espeak": espeak.phonemize,
    # "charisiu": charisiu.phonemize,
    # "goruut": goruut.phonemize,
    # "nakdimon_phonikud": nakdimon_phonikud.phonemize,
    # "dicta_phonikud": dicta_phonikud.phonemize,
    # "dicta_naive": dicta_naive.phonemize,  # Placeholder for Dicta Naive, not implemented
    # "phonikud_naive": phonikud_naive.phonemize,  # Placeholder for Phonikud Naive
    # "nakdimon_naive": nakdimon_naive.phonemize,  # Placeholder for Nakdimon Naive
}


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "out"



def ensure_dirs():
    OUTPUT_DIR.mkdir(exist_ok=True)

def phonemize_all():
    ensure_dirs()
    text_path = Path('/Volumes/Internal/audio/phonikud/phonikud_onnx/phonikud-experiments-backup/tts/ilspeech_seed0_ran_v8_sentences.json')
    with text_path.open("r", encoding="utf-8") as f:
        text_data = json.load(f)

    results = {}
    for text, _ in tqdm(text_data.items(), desc='Phonemize'):
        phonemized_versions = {}
        for name, phonemize_func in phonemizers.items():
            phonemized_versions[name] = phonemize_func(text)
        phonemized_versions["text"] = text
        results[text] = phonemized_versions

    out_path = OUTPUT_DIR / "phonemized.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ Phonemized text saved to {out_path}")

def compute_report():
    ensure_dirs()

    phonemized_path = OUTPUT_DIR / "phonemized.json"
    reference_path = Path('/Volumes/Internal/audio/phonikud/phonikud_onnx/phonikud-experiments-backup/tts/ilspeech_seed0_ran_v8_sentences.json')
    report_path = OUTPUT_DIR / "phonemize_report.json"

    with phonemized_path.open("r", encoding="utf-8") as f:
        pred_data = json.load(f)
    with reference_path.open("r", encoding="utf-8") as f:
        ref_data = json.load(f)

    # Get phonemizer names from first pred_data entry
    first_pred = next(iter(pred_data.values()), None)
    if not first_pred:
        print("No predictions found.")
        return
    phonemizers = first_pred.keys()

    total_cer = {name: 0.0 for name in phonemizers}
    total_wer = {name: 0.0 for name in phonemizers}
    total_wer_nostress = {name: 0.0 for name in phonemizers}
    individual_scores = {}
    count = 0

    for wav_id, ref in ref_data.items():
        if wav_id not in pred_data:
            continue
        pred = pred_data[wav_id]

        cer_scores = {}
        wer_scores = {}
        wer_nostress_scores = {}

        for name in phonemizers:
            pred_phonemes = pred.get(name, "")
            cer_score = cer(ref, pred_phonemes)
            wer_score = wer(ref, pred_phonemes)

            # Remove primary stress marker U+02C8 (ˈ)
            ref_nostress = ref.replace('\u02c8', '')
            pred_nostress = pred_phonemes.replace('\u02c8', '')
            wer_nostress_score = wer(ref_nostress, pred_nostress)

            total_cer[name] += cer_score
            total_wer[name] += wer_score
            total_wer_nostress[name] += wer_nostress_score

            cer_scores[name] = round(cer_score, 4)
            wer_scores[name] = round(wer_score, 4)
            wer_nostress_scores[name] = round(wer_nostress_score, 4)

        individual_scores[wav_id] = {
            "cer": cer_scores,
            "wer": wer_scores,
            "wer_without_stress": wer_nostress_scores,
        }
        count += 1

    avg_scores = {
        name: {
            "avg_cer": round(total_cer[name] / count, 4) if count else None,
            "avg_wer": round(total_wer[name] / count, 4) if count else None,
            "avg_wer_without_stress": round(total_wer_nostress[name] / count, 4) if count else None,
        }
        for name in phonemizers
    }

    report = {
        **avg_scores,
        "total": count,
        "individual_scores": individual_scores,
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✅ Report saved to {report_path}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hebrew phonemization pipeline")
    parser.add_argument("--phonemize", action="store_true", help="Run phonemization and save to output/phonemized.json")
    parser.add_argument("--evaluate", action="store_true", help="Compare phonemes to reference and generate report")

    args = parser.parse_args()

    if args.phonemize:
        phonemize_all()
    elif args.evaluate:
        compute_report()
    else:
        parser.print_help()
