"""Storage-specific naming utilities for consistent file naming across mission types"""

import re
from typing import Optional

from ..utils.text import extract_keywords, generate_slug


def generate_mission_filename(
    mission_type: str, subject: str, timestamp: str, extension: str = "json"
) -> str:
    """
    Generate unified filename: {mission-type}-{subject-slug}-{timestamp}.{extension}

    Args:
        mission_type: Type of mission (recon, brainstorm, review, query)
        subject: Subject text to convert to slug
        timestamp: Timestamp string (YYYY-MM-DD-HH-MM-SS format)
        extension: File extension

    Returns:
        Complete filename following unified naming pattern
    """
    subject_slug = generate_slug(subject)
    return f"{mission_type}-{subject_slug}-{timestamp}.{extension}"


def parse_mission_filename(filename: str) -> Optional[dict]:
    """
    Parse mission filename back into components.

    Args:
        filename: Filename to parse

    Returns:
        Dict with mission_type, subject_slug, timestamp, extension or None if invalid
    """
    pattern = r"^(\w+)-(.+)-(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\.(\w+)$"
    match = re.match(pattern, filename)

    if not match:
        return None

    mission_type, subject_slug, timestamp, extension = match.groups()

    return {
        "mission_type": mission_type,
        "subject_slug": subject_slug,
        "timestamp": timestamp,
        "extension": extension,
    }


def is_legacy_filename(filename: str) -> bool:
    """
    Check if filename uses old timestamp-only naming pattern.

    Args:
        filename: Filename to check

    Returns:
        True if legacy format, False if new unified format
    """
    legacy_pattern = r"^\w+-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.\w+$"
    return bool(re.match(legacy_pattern, filename))


def extract_subject_from_prompt(prompt: str) -> str:
    """
    Extract subject from mission prompt for filename generation.

    Args:
        prompt: Mission prompt text

    Returns:
        Extracted subject suitable for slug generation
    """
    return extract_keywords(prompt, max_words=6)
