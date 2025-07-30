"""
wget https://github.com/thewh1teagle/dicta-onnx/releases/download/model-files-v1.0/dicta-1.0.onnx
"""
from dicta_onnx import Dicta
import phonikud
import time

model = None

def phonemize(text: str) -> str:
    global model
    if model is None:
        model = Dicta('./dicta-1.0.onnx')

    with_diacritics = model.add_diacritics(text)
    phonemes = phonikud.phonemize(with_diacritics)
    return phonemes

if __name__ == "__main__":
    model = Dicta('./dicta-1.0.onnx')
    text = "בוקר טוב"
    start = time.time()
    with_diacritics = model.add_diacritics(text)
    end = time.time()
    print(f"Time taken to add diacritics: {end - start} seconds")
    phonemes = phonikud.phonemize(with_diacritics)
    print(phonemes)
    # Output: ['ʔaˈriːd', 'ʔan', 'ʔaˈðhab', 'ila', 'al', 'madˈrasah']