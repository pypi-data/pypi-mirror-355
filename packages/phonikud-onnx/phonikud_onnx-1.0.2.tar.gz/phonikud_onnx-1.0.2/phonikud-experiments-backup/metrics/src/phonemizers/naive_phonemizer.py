# https://en.wikipedia.org/wiki/Unicode_and_HTML_for_the_Hebrew_alphabet#Compact_table
DICT = {
    '\u05b0': '', # Shva
    '\u05b1': 'e', # Hataf Segol
    '\u05b2': 'a', # Hataf Patah
    '\u05b3': 'a', # Hataf Qamats
    '\u05b4': 'i', # Hiriq
    '\u05b5': 'e', # Tsere
    '\u05b6': 'e', # Segol`
    '\u05b7': 'a', # Patah
    '\u05b8': 'a', # Qamats
    '\u05b9': 'o', # Holam
    '\u05ba': 'o', # Holam Haser for Vav
    '\u05bb': 'u', # Qubuts
    '\u05bc': '',  # Dagesh
    
    '\u05be': '',  # Makaf
    '\u05bf': '',  # Rafe
    
    '\u05c0': '',  # Paseq
    '\u05c1': 'ʃ',  # Shin Dot
    '\u05c2': 's',  # Sin Dot
    '\u05c3': '',  # Sof Pasuq
    '\u05c4': '',  # Upper Dot
    '\u05c5': '',  # Lower Dot
    '\u05c6': '',  # Inverted Nun
    '\u05c7': 'o',  # Kamats Katan
    
    
    '\u05ab': 'ˈ', # stress
    '\u05bd': 'e',  # Meteg - shva na
    '|': ''
}

DICT.update({
    'א': 'ʔ',  # Alef
    'ב': 'b',  # Bet
    'ג': 'g',  # Gimel
    'ד': 'd',  # Dalet
    'ה': 'h',  # He
    'ו': 'v',  # Vav
    'ז': 'z',  # Zayin
    'ח': 'χ',  # Het
    'ט': 't',  # Tet
    'י': 'j',  # Yod
    'כ': 'k',  # Kaf
    'ך': 'k',  # Final Kaf
    'ל': 'l',  # Lamed
    'מ': 'm',  # Mem
    'ם': 'm',  # Final Mem
    'נ': 'n',  # Nun
    'ן': 'n',  # Final Nun
    'ס': 's',  # Samekh
    'ע': 'ʕ',  # Ayin
    'פ': 'p',  # Pe
    'ף': 'p',  # Final Pe
    'צ': 'ts', # Tsadi
    'ץ': 'ts', # Final Tsadi
    'ק': 'k',  # Qof
    'ר': 'r',  # Resh
    'ש': 'ʃ',  # Shin
    'ת': 't',  # Tav
})

def phonemize(text: str) -> str:
    phonemes = []
    for char in text:
        if char in DICT:
            phonemes.append(DICT[char])
        else:
            phonemes.append(char)
    phonemes = ''.join(phonemes)
    # Fix Shin sin
    phonemes = phonemes.replace('ʃʃ', 'ʃ').replace('ʃs', 's').replace('ss', 's')
    return phonemes