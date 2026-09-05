from __future__ import annotations

import re

_HP_MAX_REDUCTION = re.compile(
    r"\bHit Point maximum\s+(?:decreases|is reduced)\b",
    re.IGNORECASE,
)
_COMBATANT_CREATION = re.compile(
    r"\b(?:summons?|creates?)\b[^.]{0,100}\b(?:creature|monster|specter|zombie|skeleton)\b"
    r"|\brises(?:\s+\d+\s+hours?\s+later)?\s+as\s+(?:a|an)\s+[A-Za-z’'\-]+\b",
    re.IGNORECASE,
)


def survival_action_issues(actions: object) -> list[str]:
    """Fail closed on printed action riders that alter survival or combatant count."""
    text = str(actions or "")
    issues: list[str] = []
    if _HP_MAX_REDUCTION.search(text):
        issues.append("unsupported-survival-rider:hit-point-maximum-reduction")
    if _COMBATANT_CREATION.search(text):
        issues.append("unsupported-combatant-creation-action")
    return issues
