from __future__ import annotations

import re
from typing import Dict, Optional

# Regular expression to capture course labels like CS101, MATH-203, BIO 210
COURSE_PATTERN = re.compile(r"\b([A-Za-z]{2,}[\s-]?\d{2,3})\b")

# Ordered list of (pattern, type, priority)
RULES = [
    (re.compile(r"\b(exam|midterm|final|quiz)\b"), "test", 1),
    (re.compile(r"\b(homework|assignment|worksheet|hw)\b"), "homework", 2),
    (re.compile(r"\b(project|capstone|milestone)\b"), "project", 2),
    (re.compile(r"\b(class|lecture|seminar)\b"), "class", 3),
    (re.compile(r"\b(meet|meeting)\b"), "meeting", 3),
    (re.compile(r"\b(study|revision|review)\b"), "study", 2),
    (re.compile(r"\b(read|watch|video|podcast)\b"), "passive", 4),
]

DEFAULT_TYPE = "study"
DEFAULT_PRIORITY = 3


def _extract_course_label(text: str) -> Optional[str]:
    match = COURSE_PATTERN.search(text)
    if match:
        # Normalize by removing spaces and hyphens
        return re.sub(r"[\s-]", "", match.group(1)).upper()
    return None


def extract_course_label(text: str) -> Optional[str]:
    """Public helper to fetch a normalized course label from text.

    This wraps the internal ``_extract_course_label`` function so that other
    modules can reuse the same logic without depending on a private helper.
    The existing ``classify`` API remains unchanged.
    """
    return _extract_course_label(text)


def classify(title: str, description: str = "", use_llm: bool = False) -> Dict[str, Optional[str] | int]:
    """Classify a task using deterministic rules.

    A seam for a future LLM override is kept via the ``use_llm`` flag but is
    currently unused.
    """
    combined = f"{title} {description}".lower()
    task_type = DEFAULT_TYPE
    priority = DEFAULT_PRIORITY

    for pattern, ttype, prio in RULES:
        if pattern.search(combined):
            task_type = ttype
            priority = prio
            break

    course_label = _extract_course_label(f"{title} {description}")

    if use_llm:
        # Placeholder for optional LLM override in the future
        pass

    return {"type": task_type, "course_label": course_label, "priority": priority}
