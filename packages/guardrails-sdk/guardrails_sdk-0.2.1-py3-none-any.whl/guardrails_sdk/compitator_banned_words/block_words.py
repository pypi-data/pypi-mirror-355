import re
from typing import Literal

class UserInputError(Exception):
    """Exception raised for user-facing input errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

async def moderate_text(
    text: str,
    banned_words_file: str,
    competitor_words_file: str,
    action: Literal["mask", "block"] = "mask"
) -> dict:
    banned_words = _load_words(banned_words_file)
    competitor_words = _load_words(competitor_words_file)

    banned_pattern = _compile_pattern(banned_words)
    competitor_pattern = _compile_pattern(competitor_words)

    result = {
        "status": "allowed",
        "cleaned_text": text,
        "banned_words": [],
        "competitors": []
    }

    banned_matches = banned_pattern.findall(text)
    competitor_matches = competitor_pattern.findall(text)

    if banned_matches or competitor_matches:
        result["banned_words"] = banned_matches
        result["competitors"] = competitor_matches

        if action == "block":
            result["status"] = "blocked"
            result["cleaned_text"] = None
            raise UserInputError("Found blocked content")
        elif action == "mask":
            def mask_word(match): return "*" * len(match.group(0))
            text = banned_pattern.sub(mask_word, text)
            text = competitor_pattern.sub(mask_word, text)
            result["cleaned_text"] = text

    return result


def _compile_pattern(words: tuple) -> re.Pattern:
    if not words:
        return re.compile(r"$^")  # Matches nothing
    escaped = [re.escape(word) for word in words]
    pattern = r"\b(" + "|".join(escaped) + r")\b"
    return re.compile(pattern, flags=re.IGNORECASE)


def _load_words(filepath: str) -> tuple:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return tuple(word.strip().lower() for word in content.split(",") if word.strip())
    except Exception as e:
        raise ValueError(f"Error reading {filepath}: {e}")