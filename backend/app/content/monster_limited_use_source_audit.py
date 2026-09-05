from __future__ import annotations

import logging
import re
from functools import lru_cache

from app.content.monster_combat_scope import combat_math_relevant, feature_blocks
from app.content.monster_catalog import load_monster_rows
from app.content.monster_trait_source_audit import parse_trait_names
from app.domain.models import CombatantTemplate

logger = logging.getLogger(__name__)
_FIELDS = ("traits", "actions", "bonusActions", "reactions")
_CONNECTORS = frozenset({"a", "an", "and", "of", "or", "the", "to"})
_MARKER = re.compile(r"\((?:[^)]*(?:Recharge\s+\d(?:\s*[-–]\s*\d)?|\d+\s*/\s*Day)[^)]*)\)", re.I)
_RECHARGE = re.compile(r"Recharge\s+(\d)(?:\s*[-–]\s*(\d))?", re.I)


def _is_heading(value: str) -> bool:
    base = re.sub(r"\s*\([^)]*\)$", "", value).strip()
    words = base.split()
    if not words or len(value) > 100:
        return False
    return all(word.lower() in _CONNECTORS or re.fullmatch(r"[A-Z][A-Za-z’'\-]*", word) for word in words)


def _limited_headings(source: object) -> list[str]:
    text = re.sub(r"\s+", " ", str(source or "")).strip()
    if not text:
        return []
    names: list[str] = []
    for sentence in re.split(r"(?<=\.)\s+", text):
        candidate = sentence[:-1].strip() if sentence.endswith(".") else ""
        if candidate and _MARKER.search(candidate):
            if not _is_heading(candidate):
                raise ValueError(f"Limited-use marker is not on a parseable heading: {candidate!r}")
            names.append(candidate)
    if _MARKER.search(text) and not names:
        raise ValueError(f"SRD limited-use heading could not be parsed from: {text!r}")
    return names


def parse_limited_use_names(row: dict[str, object]) -> list[str]:
    names: list[str] = []
    for field in _FIELDS:
        names.extend(f"{field}:{name}" for name in _limited_headings(row.get(field, "")))
    return names


def _recharge_matches(template: CombatantTemplate, resource_id: str | None, resource_cost: int, heading: str) -> bool:
    match = _RECHARGE.search(heading)
    if not match or not resource_id or resource_cost != 1:
        return False
    resource = next((item for item in template.resources if item.id == resource_id), None)
    if resource is None or resource.max_uses != 1 or resource.recharge is None:
        return False
    minimum = int(match.group(1)); maximum = int(match.group(2) or match.group(1))
    return resource.recharge.minimum == minimum and resource.recharge.maximum == maximum and resource.recharge.die_size == 6


def _recharge_save_supported(template: CombatantTemplate, fingerprint: str) -> bool:
    section, _, heading = fingerprint.partition(":")
    if section != "actions":
        return False
    action_name = re.sub(r"\s*\([^)]*\)$", "", heading).strip()
    action = next((item for item in template.saving_throw_actions if item.name == action_name), None)
    return action is not None and _recharge_matches(template, action.resource_id, action.resource_cost, heading)


def _recharge_attack_supported(template: CombatantTemplate, fingerprint: str) -> bool:
    section, _, heading = fingerprint.partition(":")
    if section != "actions":
        return False
    action_name = re.sub(r"\s*\([^)]*\)$", "", heading).strip()
    attacks = [template.weapon_attack, *template.alternate_weapon_attacks]
    attack = next((item for item in attacks if item.weapon.name == action_name), None)
    return attack is not None and _recharge_matches(template, attack.resource_id, attack.resource_cost, heading)


def limited_use_source_relevant(row: dict[str, object], fingerprint: str) -> bool:
    section, _, heading = fingerprint.partition(":")
    source = row.get(section, "")
    headings = parse_trait_names(source, preserve_annotations=True)
    blocks = feature_blocks(source, headings)
    return combat_math_relevant(blocks[heading])


def limited_use_issues(template: CombatantTemplate, row: dict[str, object]) -> list[str]:
    """Certify modeled limited-use math; ignore limited movement/sensory/presentation features."""
    expected = parse_limited_use_names(row)
    issues: list[str] = []
    if template.source_limited_use_names != expected:
        issues.append("source-limited-use-fingerprint-mismatch")
    for name in expected:
        if _recharge_save_supported(template, name) or _recharge_attack_supported(template, name):
            continue
        if not limited_use_source_relevant(row, name):
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        issues.append(f"uncertified-limited-use:{slug}")
    return issues


@lru_cache(maxsize=1)
def _rows_by_name() -> dict[str, dict[str, object]]:
    return {str(row["name"]): row for row in load_monster_rows()}


def source_limited_use_names(name: str) -> list[str]:
    row = _rows_by_name().get(name)
    if row is None:
        raise ValueError(f"No SRD 5.2.1 source row for monster {name!r}.")
    return parse_limited_use_names(row)


def complete_monster_limited_use_fingerprints(templates: list[CombatantTemplate]) -> list[CombatantTemplate]:
    try:
        return [template.model_copy(update={"source_limited_use_names": source_limited_use_names(template.name)}) if template.kind == "monster" else template for template in templates]
    except Exception:
        logger.exception("Failed to derive canonical monster limited-use fingerprints from SRD source.")
        raise
