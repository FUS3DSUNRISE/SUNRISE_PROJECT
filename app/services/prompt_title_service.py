import re


LEADING_ACTION_RE = re.compile(
    r"^\s*(?:"
    r"please\s+)?(?:"
    r"create|generate|make|build|model|design|draw|render|produce|craft|"
    r"write\s+code\s+for|write\s+(?:a|an|the)?\s*script\s+for"
    r")\b(?:\s+(?:me|us))?(?:\s+(?:a|an|the))?\s+",
    re.IGNORECASE,
)
TRAILING_CONTEXT_RE = re.compile(
    r"\b(?:with|using|that|which|for|in|on|at|from|made\s+of|including|featuring)\b.*$",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?")
SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "nor", "of", "on", "or", "per", "the", "to", "vs", "with"}
FILLER_WORDS = {"3d", "object", "asset", "model", "simple", "basic", "plain", "realistic", "detailed", "high", "quality"}
MAX_TITLE_LENGTH = 24


def _title_case(words: list[str]) -> str:
    return " ".join(
        word.lower()
        if 0 < index < len(words) - 1 and word.lower() in SMALL_WORDS
        else "-".join(part.capitalize() for part in word.split("-"))
        for index, word in enumerate(words)
    )


def generate_prompt_title(prompt_text: str | None) -> str:
    text = TRAILING_CONTEXT_RE.sub("", LEADING_ACTION_RE.sub("", (prompt_text or "").strip(), count=1))
    words = WORD_RE.findall(text)

    while len(_title_case(words)) > MAX_TITLE_LENGTH and len(words) > 1:
        removable_index = next(
            (index for index, word in enumerate(words[:-1]) if word.lower() in FILLER_WORDS),
            None,
        )
        words.pop(removable_index if removable_index is not None else -2)

    title = _title_case(words).strip() if words else "Untitled Prompt"
    return title if len(title) <= MAX_TITLE_LENGTH else title[:MAX_TITLE_LENGTH].rstrip()
