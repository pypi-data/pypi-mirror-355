"""
wget https://github.com/thewh1teagle/nakdimon-onnx/releases/download/v0.1.0/nakdimon.onnx
"""
from nakdimon_onnx import Nakdimon
import phonikud

model = None

def phonemize(text: str) -> str:
    global model
    if model is None:
        model = Nakdimon("nakdimon.onnx")

    with_diacritics = model.compute(text)
    phonemes = phonikud.phonemize(with_diacritics)
    return phonemes

if __name__ == "__main__":
    model = Nakdimon("nakdimon.onnx")
    text = "בוקר טוב"
    with_diacritics = model.compute(text)
    phonemes = phonikud.phonemize(with_diacritics)
    print(phonemes)
    # Output: ['ʔaˈriːd', 'ʔan', 'ʔaˈðhab', 'ila', 'al', 'madˈrasah']