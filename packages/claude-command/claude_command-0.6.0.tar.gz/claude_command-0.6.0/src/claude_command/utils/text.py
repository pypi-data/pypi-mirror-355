"""General text processing utilities"""

import re


def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate a URL-safe slug from text.

    Args:
        text: The input text
        max_length: Maximum length of the slug

    Returns:
        A kebab-case slug suitable for filenames/URLs
    """
    if not text:
        return "untitled"

    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", " ", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    slug = slug.strip("-")

    if len(slug) > max_length:
        truncated = slug[:max_length]
        last_hyphen = truncated.rfind("-")
        if last_hyphen > max_length // 2:
            slug = truncated[:last_hyphen]
        else:
            slug = truncated

    return slug if slug else "untitled"


def extract_keywords(text: str, max_words: int = 8) -> str:
    """
    Extract meaningful keywords from text by removing filler words.

    Args:
        text: The input text
        max_words: Maximum number of words to extract

    Returns:
        Extracted keywords as string
    """
    if not text:
        return "untitled"

    filler_words = {
        "what",
        "how",
        "why",
        "when",
        "where",
        "who",
        "which",
        "can",
        "could",
        "would",
        "should",
        "are",
        "is",
        "do",
        "does",
        "did",
        "will",
        "have",
        "has",
        "had",
        "be",
        "been",
        "being",
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "among",
        "amongst",
        "within",
        "without",
        "please",
        "help",
        "me",
        "you",
        "your",
        "my",
        "i",
        "we",
        "us",
        "our",
        "this",
        "that",
        "these",
        "those",
    }

    words = re.findall(r"\b\w+\b", text.lower())
    filtered_words = [w for w in words if len(w) > 1 and w not in filler_words]
    subject_words = filtered_words[:max_words]

    return (
        " ".join(subject_words) if subject_words else " ".join(text.split()[:max_words])
    )
