from __future__ import annotations

import logging
import re
from functools import lru_cache

from app.content.monster_combat_scope import combat_math_relevant, feature_blocks
from app.content.monster_catalog import load_monster_rows
from app.content.monster_trait_source_audit import parse_trait_names
from app.domain.models import CombatantTemplate

logger = logging.getLogger(__name__)
_USES = re.compile(r"\bLegendary Action Uses:\s*(\d+)\.", re.I)


def parse_legendary_action_names(source_legendary_actions: object) -> list[str]:
    """Retain the printed legendary use count plus every action heading."""
    text = str(source_legendary_actions or "").strip()
    if not text:
        return []
    match = _USES.search(text)
    if not match:
        raise ValueError(f"Legendary Action Uses could not be parsed from: {text!r}")
    actions = parse_trait_names(text)
    if not actions:
        raise ValueError(f"Legendary action headings could not be parsed from: {text!r}")
    return [f"uses:{int(match.group(1))}", *actions]


def legendary_source_relevant(source_legendary_actions: object) -> bool:
    text = str(source_legendary_actions or "").strip()
    if not text:
        return False
    headings = parse_trait_names(text, preserve_annotations=True)
    blocks = feature_blocks(text, headings)
    return any(combat_math_relevant(blocks[name]) for name in headings)


def legendary_action_issues(template: CombatantTemplate, row: dict[str, object]) -> list[str]:
    """Block legendary economy only when a legendary option changes Iron Pit combat math."""
    source = row.get("legendaryActions", "")
    expected = parse_legendary_action_names(source)
    issues: list[str] = []
    if template.source_legendary_action_names != expected:
        issues.append("source-legendary-action-fingerprint-mismatch")
    if expected and legendary_source_relevant(source):
        issues.append("uncertified-legendary-action-economy")
    return issues


@lru_cache(maxsize=1)
def _rows_by_name() -> dict[str, dict[str, object]]:
    return {str(row["name"]): row for row in load_monster_rows()}


def source_legendary_action_names(name: str) -> list[str]:
    row = _rows_by_name().get(name)
    if row is None:
        raise ValueError(f"No SRD 5.2.1 source row for monster {name!r}.")
    return parse_legendary_action_names(row.get("legendaryActions", ""))


def complete_monster_legendary_fingerprints(templates: list[CombatantTemplate]) -> list[CombatantTemplate]:
    try:
        return [
            template.model_copy(update={"source_legendary_action_names": source_legendary_action_names(template.name)})
            if template.kind == "monster" else template
            for template in templates
        ]
    except Exception:
        logger.exception("Failed to derive canonical monster legendary-action fingerprints from SRD source.")
        raise
