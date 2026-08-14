import math
from typing import Tuple


def call_mock_provider(model: str, text: str) -> Tuple[str, int]:
    """Deterministic mock provider: echo text, tokens ~= words rounded to 100."""
    words = text.split()
    tokens = max(len(words), 1)
    output = f"[{model}] {text}"
    token_units = int(math.ceil(tokens / 100.0) * 100)
    return output, token_units
