
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM

BIAS_PREFIXES = {
    "en": "The following text contains gender stereotypes: ",
    "ur": "درج ذیل متن میں صنفی دقیانوسی تصورات موجود ہیں: ",
}

class SelfDebiasModel:
    def __init__(self, model_name="xlm-roberta-base",
                 lang="en", decay=50.0, epsilon=0.01):
        if lang not in BIAS_PREFIXES:
            raise ValueError("Language must be 'en' or 'ur'")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForMaskedLM.from_pretrained(
            model_name
        ).to(self.device).eval()
        self.lang = lang
        self.decay = decay
        self.epsilon = epsilon

    @torch.inference_mode()
    def predict(self, sentence, top_k=3):
        tok = self.tokenizer

        if sentence.count(tok.mask_token) != 1:
            raise ValueError("Expected exactly one mask")

        def probabilities(text):
            inputs = tok(text, return_tensors="pt").to(self.device)
            positions = (
                inputs["input_ids"][0] == tok.mask_token_id
            ).nonzero(as_tuple=True)[0]

            if len(positions) != 1:
                raise ValueError("Expected exactly one mask")

            logits = self.model(**inputs).logits[0, positions[0]]
            return torch.softmax(logits.float(), dim=-1)

        base = probabilities(sentence)
        biased = probabilities(BIAS_PREFIXES[self.lang] + sentence)

        # Self-Debiasing-inspired decay:
        # suppress tokens more probable under the bias prefix.
        difference = base - biased

        scaling = torch.where(
            difference >= 0,
            torch.ones_like(difference),
            torch.maximum(
                torch.exp(self.decay * difference),
                torch.full_like(difference, self.epsilon)
            )
        )

        adjusted = base * scaling
        adjusted = adjusted / adjusted.sum()

        values, ids = torch.topk(adjusted, top_k)

        return [
            {
                "token_str": tok.decode([int(i)]).strip(),
                "score": float(v)
            }
            for i, v in zip(ids, values)
        ]
