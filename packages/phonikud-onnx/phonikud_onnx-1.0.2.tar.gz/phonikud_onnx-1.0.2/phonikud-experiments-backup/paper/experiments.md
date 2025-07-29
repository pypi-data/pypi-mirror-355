# Experiments

Text = שלום וברכה ניפרד בשמחה ממומין

Machine: 
    macOS M1

Phonikud:
    phonikud phonemize: 0.05s
    
Piper medium:
    inference: 0.09s duration: 2.65s

StyleTTS2:
    inference: 1.58s, duration: 3.23s

Dicta:
    inference: 0.08s

MMS:
    inference: 0.64s duration: 3.35s

Saspeech:
    inference: 0.28s duration: 2.17s

Results:
    Phonikud Piper RTF: (0.09+0.05) / 2.65 = 0.05
    StyleTTS2 RTF: (1.58+0.05) / 3.23 = 0.50
    Dicta MMS RTF: (0.64 + 0.08) / 3.35 = 0.21
    Dicta Saspeech RTF: (0.28+0.08) / 2.17 = 0.16
    LoTHM RTF: 84.75 
    HebTTS RTF: 25.44
    RoboShaul RTF: 1.58

    

