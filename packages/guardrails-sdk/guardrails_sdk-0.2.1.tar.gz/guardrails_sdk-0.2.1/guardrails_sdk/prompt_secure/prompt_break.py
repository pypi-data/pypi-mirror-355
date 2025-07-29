from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load tokenizer and model (adjust this to your actual model if hosted on Hugging Face Hub or local path)
# replace with actual model path or name
model_name = "protectai/deberta-v3-base-prompt-injection-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)


async def classify_prompt_injection(text: str):
    inputs = tokenizer(text, return_tensors="pt",
                       truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1).squeeze()

    # Assuming binary classification: [0] -> safe, [1] -> injection
    is_injection = torch.argmax(probs).item() == 1
    confidence = probs[1].item()
    return {
        "is_prompt_injection": is_injection,
        "confidence": confidence,
        "probabilities": probs.tolist()
    }


