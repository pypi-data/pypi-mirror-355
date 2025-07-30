"""
wget https://huggingface.co/thewh1teagle/phonikud-onnx/resolve/main/phonikud-1.0.int8.onnx
"""
from phonikud_onnx import Phonikud
import phonikud

phonikud_model = None

def phonemize(text: str) -> str:
    global phonikud_model
    if phonikud_model is None:
        phonikud_model = Phonikud("/Volumes/Internal/audio/phonikud/phonikud_onnx/phonikud-1.0.int8.onnx")

    with_diacritics = phonikud_model.add_diacritics(text)
    phonemes = phonikud.phonemize(with_diacritics)
    return phonemes
