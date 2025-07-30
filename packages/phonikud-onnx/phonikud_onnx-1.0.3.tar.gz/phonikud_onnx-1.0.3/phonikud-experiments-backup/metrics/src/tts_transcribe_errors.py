"""
uv sync

# MMS
uv run src/tts_transcribe_errors.py --mode transcribe --input_folder ../mms_wav --transcripts_path mms_transcript.json
uv run src/tts_transcribe_errors.py --mode wer --ref_path ./data/text_hand.json --transcripts_path mms_transcript.json --report_path mms_report.json

# Piper
uv run src/tts_transcribe_errors.py --mode transcribe --input_folder ../tts/piper_wav --transcripts_path piper_transcript.json
uv run src/tts_transcribe_errors.py --mode wer --ref_path ./data/text_hand.json --transcripts_path piper_transcript.json --report_path piper_report.json
"""
from transcribe import Transcriber
from tqdm import tqdm
from pathlib import Path
import json
import argparse
from jiwer import wer, cer
import re


def compute_error_scores(refs, hyps):
    """
    Compute WER and CER for a list of reference and hypothesis sentences.
    """
    if len(refs) != len(hyps):
        raise ValueError("Mismatched list lengths.")
    
    wer_individual = [wer(r, h) for r, h in zip(refs, hyps)]
    cer_individual = [cer(r, h) for r, h in zip(refs, hyps)]

    wer_avg = sum(wer_individual) / len(wer_individual)
    cer_avg = sum(cer_individual) / len(cer_individual)

    wer_global = wer(" ".join(refs), " ".join(hyps))
    cer_global = cer(" ".join(refs), " ".join(hyps))

    return (wer_avg, wer_global, dict(zip(refs, wer_individual)),
            cer_avg, cer_global, dict(zip(refs, cer_individual)))


def transcribe_folder(src_folder: str, dst_path: str, transcriber):
    files = list(Path(src_folder).glob('*.wav'))
    data = {}
    for file in tqdm(files, desc='Transcribing'):
        transcript = transcriber.transcribe(str(file))
        data[file.stem] = transcript
        
        # Sort data by integer key before writing
        sorted_data = dict(sorted(data.items(), key=lambda item: int(item[0])))
        
        with open(dst_path, 'w', encoding='utf-8') as fp:
            json.dump(sorted_data, fp, indent=4, ensure_ascii=False)
            fp.flush()
    return data


def compute_wer(refs: dict, hyps: dict):
    keys = sorted(set(refs.keys()) & set(hyps.keys()))
    ref_texts = [refs[k] for k in keys]
    hyp_texts = [hyps[k] for k in keys]
    
    


    wer_avg, wer_global, wer_indiv, cer_avg, cer_global, cer_indiv = compute_error_scores(ref_texts, hyp_texts)
    return wer_avg, wer_global, dict(zip(keys, wer_indiv.values())), \
           cer_avg, cer_global, dict(zip(keys, cer_indiv.values()))


def create_report(report_path: str, wer_avg: float, wer_global: float, wer_indiv: dict,
                  cer_avg: float, cer_global: float, cer_indiv: dict):
    report = {
        "average_wer": wer_avg,
        "global_wer": wer_global,
        "wer_accuracy_percent": round((1 - wer_global) * 100, 2),

        "average_cer": cer_avg,
        "global_cer": cer_global,
        "cer_accuracy_percent": round((1 - cer_global) * 100, 2),

        "individual_wers": wer_indiv,
        "individual_cers": cer_indiv,
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    print(f"Report saved to {report_path}")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['transcribe', 'wer'], required=True)
    parser.add_argument('--input_folder', help='Path to folder with .wav files')
    parser.add_argument('--transcripts_path', help='Path to save/load transcripts (JSON)')
    parser.add_argument('--ref_path', help='Path to human references (JSON)')
    parser.add_argument('--report_path', help='Path to save WER report (JSON)')
    args = parser.parse_args()

    if args.mode == 'transcribe':
        transcriber = Transcriber()
        if not args.input_folder or not args.transcripts_path:
            raise ValueError("input_folder and transcripts_path are required for transcription")
        transcribe_folder(args.input_folder, args.transcripts_path, transcriber)

    elif args.mode == 'wer':
        if not args.ref_path or not args.transcripts_path or not args.report_path:
            raise ValueError("ref_path, transcripts_path, and report_path are required for WER computation")

        with open(args.ref_path, encoding='utf-8') as f:
            refs = json.load(f)
        with open(args.transcripts_path, encoding='utf-8') as f:
            hyps = json.load(f)

        # Remove nikud
        refs = {k: re.sub(r'[\u05b0-\u05c7]', '', v.strip()) for k, v in refs.items()}
        hyps = {k: re.sub(r'[\u05b0-\u05c7]', '', v.strip()) for k, v in hyps.items()}
        
        for k, v in refs.items():
            if len(v.split()) < 6:
                # breakpoint()
                refs[k] = ' '.join([v] * 2) # piper doesn't work well with short sentences
        

        # Print example
        print(f"Example reference: {list(refs.values())[0]}")
        print(f"Example hypothesis: {list(hyps.values())[0]}")
        
        wer_avg, wer_glob, wer_indiv, cer_avg, cer_glob, cer_indiv = compute_wer(refs, hyps)
        create_report(args.report_path, wer_avg, wer_glob, wer_indiv, cer_avg, cer_glob, cer_indiv)


if __name__ == "__main__":
    main()
