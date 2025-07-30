import phonemizer
from phonemizer.backend.espeak.wrapper import EspeakWrapper
import espeakng_loader

# Setup espeak library and data paths (run once)
EspeakWrapper.set_library(espeakng_loader.get_library_path())
EspeakWrapper.set_data_path(espeakng_loader.get_data_path())

def phonemize(text: str) -> str:
    """
    Phonemize Hebrew text using espeak backend.

    Args:
        text (str): Hebrew input text.

    Returns:
        str: Phonemized output.
    """
    phonemes = phonemizer.phonemize(text, language="he", backend="espeak")
    # Clean output from unknown markers like (en)_(he)
    import re
    phonemes = re.sub(r'\([a-z]+\).+\([a-z]+\)', '', phonemes)
    return phonemes
