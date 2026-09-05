from __future__ import annotations

import logging
import re
from functools import lru_cache

from app.content.monster_combat_scope import combat_math_relevant, feature_blocks
from app.content.monster_catalog import load_monster_rows
from app.domain.models import CombatantTemplate
from app.domain.traits import CombatTrait

logger = logging.getLogger(__name__)
_CONNECTORS = frozenset({"a", "an", "and", "of", "or", "the", "to"})
_MODELED_TRAITS = {
    "Pack Tactics": CombatTrait.PACK_TACTICS,
    "Bloodied Fury": CombatTrait.BLOODIED_FURY,
    "Swarm": CombatTrait.SWARM,
    "Undead Fortitude": CombatTrait.UNDEAD_FORTITUDE,
}
_ARENA_NEUTRAL_TRAITS = frozenset({
    "Agile", "Amphibious", "Beast of Burden", "False Appearance", "Flyby", "Hellish Restoration",
    "Hold Breath", "Ice Walk", "Illumination", "Jumper", "Keen Hearing", "Keen Hearing and Sight",
    "Keen Hearing and Smell", "Keen Sight", "Keen Smell", "Mimicry", "Running Leap", "Spider Climb",
    "Standing Leap", "Sunlight Sensitivity", "Training", "Water Breathing", "Web Walker",
})


def _normalized_heading(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)$", "", value).strip()


def _is_heading(value: str) -> bool:
    if not value or len(value) > 80:
        return False
    plain = _normalized_heading(value)
    if any(mark in plain for mark in ",:;!?"):
        return False
    words = plain.split()
    if not words:
        return False
    for word in words:
        if word.lower() in _CONNECTORS:
            continue
        if not re.fullmatch(r"[A-Z][A-Za-z’'\-]*", word):
            return False
    return True


def parse_trait_names(source_traits: object, *, preserve_annotations: bool = False) -> list[str]:
    text = str(source_traits or "").strip()
    if not text:
        return []
    names: list[str] = []
    for sentence in re.split(r"(?<=\.)\s+", text):
        candidate = sentence[:-1].strip() if sentence.endswith(".") else ""
        if _is_heading(candidate):
            names.append(candidate if preserve_annotations else _normalized_heading(candidate))
    if not names:
        raise ValueError(f"SRD trait headings could not be parsed from: {text!r}")
    return names


def combat_relevant_trait_names(source_traits: object) -> set[str]:
    """Return unmodeled trait headings whose prose can change Iron Pit combat math."""
    annotated = parse_trait_names(source_traits, preserve_annotations=True)
    blocks = feature_blocks(source_traits, annotated)
    return {
        _normalized_heading(name)
        for name in annotated
        if combat_math_relevant(blocks[name])
    }


def trait_issues(template: CombatantTemplate, row: dict[str, object]) -> list[str]:
    expected = parse_trait_names(row.get("traits", ""))
    issues: list[str] = []
    if template.source_trait_names != expected:
        issues.append("source-trait-fingerprint-mismatch")
    for source_name, runtime_trait in _MODELED_TRAITS.items():
        source_has = source_name in expected
        runtime_has = runtime_trait in template.combat_traits
        if source_has and not runtime_has:
            issues.append(f"trait-runtime-missing:{runtime_trait.value}")
        elif runtime_has and not source_has:
            issues.append(f"trait-source-missing:{runtime_trait.value}")
    certified = set(_MODELED_TRAITS) | set(_ARENA_NEUTRAL_TRAITS)
    relevant = combat_relevant_trait_names(row.get("traits", ""))
    for name in expected:
        if name in certified or name not in relevant:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        issues.append(f"uncertified-trait:{slug}")
    return issues


@lru_cache(maxsize=1)
def _rows_by_name() -> dict[str, dict[str, object]]:
    return {str(row["name"]): row for row in load_monster_rows()}


def source_trait_names(name: str) -> list[str]:
    row = _rows_by_name().get(name)
    if row is None:
        raise ValueError(f"No SRD 5.2.1 source row for monster {name!r}.")
    return parse_trait_names(row.get("traits", ""))


def complete_monster_trait_fingerprints(templates: list[CombatantTemplate]) -> list[CombatantTemplate]:
    try:
        return [
            template.model_copy(update={"source_trait_names": source_trait_names(template.name)})
            if template.kind == "monster" else template
            for template in templates
        ]
    except Exception:
        logger.exception("Failed to derive canonical monster trait fingerprints from SRD source.")
        raise
