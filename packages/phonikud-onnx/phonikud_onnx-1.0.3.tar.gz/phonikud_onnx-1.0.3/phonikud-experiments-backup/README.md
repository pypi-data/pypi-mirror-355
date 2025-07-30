# phonikud-paper

Academic paper of Phonikud: Hebrew G2P

See [phonikud](https://github.com/thewh1teagle/phonikud) on Github

[▶️ Run in Colab](./paper/notebook.ipynb)


# TODO

- Phonemized and non phonemized models
- Metrics on the two models Plus other models such as MMS using ASR + WER
- Add metrics and code to the repo
- Create paper intro page
- Finish correcting RanSpeech dataset
- Finalize paper 📜
- Inspire from [adiyoss-lab/HebTTS](https://pages.cs.huji.ac.il/adiyoss-lab/HebTTS)

# Notes

- Add credit to Dicta
- Mention relevant speech and phonetics datasets

# Good points

1. By using phonemes, we can fine-tune an English model with minimal data and compute resources.
2. The use of unambiguous phonemes allows the model to learn in a simple yet precise way - it doesn’t get confused like large models. Accuracy depends entirely on the inference input, not on training.
3. We've introduced a new method where phonetic features like stress are tagged at the word level rather than the phoneme level. This makes annotation easier, more readable, and more data-efficient.
4. The approach can serve as a foundation for building an end-to-end text to phoneme model, bootstrapped directly from the library.
5. The model is lightweight enough to run locally on mobile devices, web browsers, and standard computers - while delivering near cloud level quality.
5. By handling everything in text, we can add a lightweight multilingual LLM expander to convert numbers, emojis, dates, times, and more into speech friendly forms making the system flexible and modular for easy improvements without relying on large, complex models.
6. We learned that for bootstrapping challenging text-to-phoneme and text normalization tasks, test-driven development is key - creating tests early and iteratively refining the code ensures balanced, reliable progress.
7. We invented diacritics to tag missing features like stress that don’t have existing diacritics. This method can be applied to other languages and works well with BERT/transformer models that learn from text and context.
