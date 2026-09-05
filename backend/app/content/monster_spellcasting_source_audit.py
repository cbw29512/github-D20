from __future__ import annotations

import hashlib
import logging
import re
from functools import lru_cache

from app.content.monster_catalog import load_monster_rows
from app.domain.models import CombatantTemplate

logger = logging.getLogger(__name__)
_FIELDS = ("traits", "actions", "bonusActions", "reactions")
_CASTING = re.compile(r"\bSpellcasting\b|\bcast(?:s|ing)?\b", re.IGNORECASE)
_SPELL_GROUP = re.compile(
    r"\b(?:At Will|\d+/Day(?: Each)?):\s*(.*?)(?=\s+(?:At Will|\d+/Day(?: Each)?):|$)",
    re.IGNORECASE,
)
_NEXT_ACTION_FEATURE = re.compile(
    r"\s+[A-Z][A-Za-z’' -]{1,80}\.\s+"
    r"(?:(?:Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+Saving Throw:"
    r"|(?:Melee|Ranged|Melee or Ranged)\s+Attack Roll:|Trigger:|Response:)",
)
# Explicitly certified as irrelevant to the standard flat/open Iron Pit outcome.
# These spells are never selected as combat actions; unknown additions fail closed.
_ARENA_NEUTRAL_SPELLS = frozenset({"Detect Evil and Good", "Detect Magic", "Clairvoyance"})


def _normalized(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def spellcasting_source_text(row: dict[str, object]) -> str:
    """Retain complete source sections that contain casting rules, not guessed spell metadata."""
    chunks: list[str] = []
    for field in _FIELDS:
        text = _normalized(row.get(field, ""))
        if text and _CASTING.search(text):
            chunks.append(f"{field}={text}")
    return "\n".join(chunks)


def spellcasting_fingerprint(row: dict[str, object]) -> str | None:
    text = spellcasting_source_text(row)
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None


def _outside_parentheses_prefix(text: str) -> str:
    """Bound a printed spell list before punctuation or the next action feature."""
    depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
            continue
        if char == ")" and depth:
            depth -= 1
            continue
        if depth:
            continue
        if _NEXT_ACTION_FEATURE.match(text, index):
            return text[:index]
        if char == ".":
            return text[:index]
    return text


def _split_outside_parentheses(text: str) -> list[str]:
    """Split spell-list commas without splitting explanatory spell parentheses."""
    parts: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def printed_spell_names(row: dict[str, object]) -> set[str]:
    """Extract only spell-list entries; never consume prose from the next feature."""
    text = spellcasting_source_text(row)
    spells: set[str] = set()
    for group in _SPELL_GROUP.findall(text):
        bounded = _outside_parentheses_prefix(group)
        spells.update(_split_outside_parentheses(bounded))
    return spells


def arena_neutral_spellcasting(row: dict[str, object]) -> bool:
    """True only when every parsed printed spell is explicitly certified arena-neutral."""
    spells = printed_spell_names(row)
    return bool(spells) and spells <= _ARENA_NEUTRAL_SPELLS


def spellcasting_issues(template: CombatantTemplate, row: dict[str, object]) -> list[str]:
    """Fail closed on combat casting while allowing explicitly certified noncombat spell lists."""
    expected = spellcasting_fingerprint(row)
    issues: list[str] = []
    if template.source_spellcasting_fingerprint != expected:
        issues.append("source-spellcasting-fingerprint-mismatch")
    if expected is not None and not arena_neutral_spellcasting(row):
        issues.extend(("uncertified-monster-spellcasting", "spell-concentration-source-not-vendored"))
    return issues


@lru_cache(maxsize=1)
def _rows_by_name() -> dict[str, dict[str, object]]:
    return {str(row["name"]): row for row in load_monster_rows()}


def source_spellcasting_fingerprint(name: str) -> str | None:
    row = _rows_by_name().get(name)
    if row is None:
        raise ValueError(f"No SRD 5.2.1 source row for monster {name!r}.")
    return spellcasting_fingerprint(row)


def complete_monster_spellcasting_fingerprints(templates: list[CombatantTemplate]) -> list[CombatantTemplate]:
    try:
        return [
            template.model_copy(update={"source_spellcasting_fingerprint": source_spellcasting_fingerprint(template.name)})
            if template.kind == "monster" else template
            for template in templates
        ]
    except Exception:
        logger.exception("Failed to derive canonical monster spellcasting fingerprints from SRD source.")
        raise
