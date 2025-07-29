"""
uv pip install pygoruut       
"""
"""
uv pip install pygoruut       
"""
from pygoruut.pygoruut import Pygoruut

pygoruut = None

def phonemize(sentence: str) -> str:
    global pygoruut
    if pygoruut is None:
        pygoruut = Pygoruut()

    return str(pygoruut.phonemize(language="Hebrew", sentence=sentence))

# Example usage:
if __name__ == "__main__":
    print(phonemize("בוקר טוב"))
