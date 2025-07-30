"""
wget https://huggingface.co/thewh1teagle/phonikud-onnx/resolve/main/phonikud-1.0.int8.onnx
"""
from phonikud_onnx import Phonikud
from phonemizers import naive_phonemizer
# import naive_phonemizer

phonikud_model = None

def phonemize(text: str) -> str:
    global phonikud_model
    if phonikud_model is None:
        phonikud_model = Phonikud("phonikud-1.0.int8.onnx")

    with_diacritics = phonikud_model.add_diacritics(text)
    phonemes = naive_phonemizer.phonemize(with_diacritics)
    return phonemes


if __name__ == "__main__":
    phonikud_model = Phonikud("phonikud-1.0.int8.onnx")
    text = "בוקר טוב"
    with_diacritics = phonikud_model.add_diacritics(text)
    phonemes = naive_phonemizer.phonemize(with_diacritics)
    print(phonemes)
    # Output: ['ʔaˈriːd', 'ʔan', 'ʔaˈðhab', 'ila', 'al', 'madˈrasah']