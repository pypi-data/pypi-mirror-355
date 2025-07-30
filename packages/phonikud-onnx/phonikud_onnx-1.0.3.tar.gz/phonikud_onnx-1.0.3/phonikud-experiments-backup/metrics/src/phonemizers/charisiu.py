from transformers import T5ForConditionalGeneration, AutoTokenizer
import torch

model = None
tokenizer = None

def phonemize(sentence: str) -> str:
    global model, tokenizer
    if model is None or tokenizer is None:
        model = T5ForConditionalGeneration.from_pretrained('charsiu/g2p_multilingual_byT5_small_100')
        tokenizer = AutoTokenizer.from_pretrained('google/byt5-small')

    words = sentence.split()
    words = ['<heb-il>: '+i for i in words]

    with torch.no_grad():
        out = tokenizer(words,padding=True,add_special_tokens=False,return_tensors='pt')
        preds = model.generate(**out,num_beams=1,max_length=50) # We do not find beam search helpful. Greedy decoding is enough. 
        phones = tokenizer.batch_decode(preds.tolist(),skip_special_tokens=True)
    return ' '.join(phones)

if __name__ == "__main__":
    sentence = "בוקר טוב"
    phonemes = phonemize(sentence)
    print(f"Phonemized sentence: {phonemes}")
