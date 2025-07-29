import argparse
import json
from pathlib import Path
from jiwer import cer, wer
from tqdm import tqdm

from phonemizers import charisiu, phonikud_phonemizer, espeak, goruut, nakdimon_phonikud, dicta_phonikud, dicta_naive, nakdimon_naive, phonikud_naive

phonemizers = {
    "phonikud": phonikud_phonemizer.phonemize,
    "espeak": espeak.phonemize,
    "charisiu": charisiu.phonemize,
    "goruut": goruut.phonemize,
    "nakdimon_phonikud": nakdimon_phonikud.phonemize,
    "dicta_phonikud": dicta_phonikud.phonemize,
    "dicta_naive": dicta_naive.phonemize,  # Placeholder for Dicta Naive, not implemented
    "phonikud_naive": phonikud_naive.phonemize,  # Placeholder for Phonikud Naive
    "nakdimon_naive": nakdimon_naive.phonemize,  # Placeholder for Nakdimon Naive
}

text = "בוקר טוב"
text = """
רוח הצפון והשמש התוכחו בניהם מי מהם חזק יותר. גמרו, כי את הנצחון ינחל מי שיצליח לפשוט מעל עובר אורח את בגדיו. פתח רוח הצפון ונשב בחזקה. הידק האדם את בגדיו אל גופו. אז הסתער עליו הרוח ביתר עוז, אך האדם, משהוסיף הקור לענותו, לבש מעיל עליון על בגדיו. נואש ממנו הרוח ומסרו בידי השמש.
תחילה זרח עליו השמש ברכות, והאדם הסיר את בגדו העליון מעליו. הגביר השמש את חמו, עד שלא יכול האדם לעמוד בפני השרב, ופשט את הגדיו ונכנס לתוך הנהר, שהיה בקרבת מקום, כדי לרחוץ במימיו.
""".strip()
for k,func in phonemizers.items():
    print(f"{k}\n{func(text)}")
    