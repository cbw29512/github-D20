from __future__ import annotations

import json
import re

from app.content.arena_eligibility import deferred_environment_reason
from app.content.monster_bonus_action_source_audit import arena_neutral_bonus_action_source
from app.content.monster_catalog import build_monster_catalog, load_monster_rows
from app.content.monster_combat_scope import combat_math_relevant
from app.content.monster_defense_source_audit import parse_defense_profile
from app.content.monster_legendary_source_audit import legendary_source_relevant
from app.content.monster_limited_use_source_audit import limited_use_source_relevant, parse_limited_use_names
from app.content.monster_reaction_source_audit import (
    arena_neutral_reaction_source,
    parse_parry_ac_bonus,
    parse_reaction_names,
    parse_redirect_attack_range,
)
from app.content.monster_spellcasting_source_audit import arena_neutral_spellcasting, spellcasting_fingerprint
from app.content.monster_trait_source_audit import _ARENA_NEUTRAL_TRAITS, _MODELED_TRAITS, combat_relevant_trait_names
from app.domain.catalog import CoverageStatus

_CONDITION_OR_CONTROL = re.compile(
    r"\b(blinded|charmed|frightened|incapacitated|paralyzed|petrified|poisoned|prone|restrained|stunned|unconscious|swallow(?:s|ed)?)\b",
    re.I,
)
_COMPLEX_ACTION = re.compile(
    r"\b(Saving Throw|Failure:|Success:|Temporary Hit Points?|regains?\s+\d+|Concentration)\b",
    re.I,
)
_DAMAGE_TYPES = r"Acid|Bludgeoning|Cold|Fire|Force|Lightning|Necrotic|Piercing|Poison|Psychic|Radiant|Slashing|Thunder"
_SUPPORTED_BLOODIED_REPLACEMENT = re.compile(
    rf"\bdamage,?\s+or\s+\d+\s*\(\s*\d+\s*d\s*\d+(?:\s*[+-]\s*\d+)?\s*\)\s+"
    rf"(?:{_DAMAGE_TYPES})\s+damage\s+if\s+the\s+[a-z][a-z -]*\s+is\s+Bloodied\b",
    re.I,
)
_SUPPORTED_FIXED_ON_HIT = re.compile(rf"\bplus\s+\d+\s+(?:{_DAMAGE_TYPES})\s+damage\b", re.I)
_HIDDEN_RIDER = re.compile(
    r"\bnext attack roll\b"
    r"|\bHit Point maximum\s+(?:decreases|is reduced)\b"
    r"|\b(?:summons?|creates?)\b[^.]{0,100}\b(?:creature|monster|specter|zombie|skeleton)\b"
    r"|\brises(?:\s+\d+\s+hours?\s+later)?\s+as\s+(?:a|an)\s+[A-Za-z’'\-]+\b"
    r"|\bdamage,?\s+or\s+\d+\s*\([^)]*\)\s+\w+\s+damage\s+if\b"
    rf"|\bplus\s+\d+\s+(?:{_DAMAGE_TYPES})\s+damage\b",
    re.I,
)
_ATTACK_ROLL = re.compile(r"\b(?:Melee|Ranged|Melee or Ranged)\s+Attack Roll:", re.I)
_ALLOWED_TRAITS = set(_ARENA_NEUTRAL_TRAITS) | set(_MODELED_TRAITS)
_DETAIL_FIELDS = ("name", "size", "armorClass", "hitPoints", "speed", "challenge", "traits", "actions")
_DETAIL_BLOCKER_LIMIT = 30
_NONCOMBAT = "deferred-arena:noncombat-only"


def _has_neighbor_bleed(row: dict[str, object], monster_names: set[str]) -> bool:
    actions = str(row.get("actions", "")).rstrip()
    own_name = str(row.get("name", ""))
    return any(name != own_name and actions.endswith(name) for name in monster_names)


def _reaction_is_modeled(row: dict[str, object], reactions: list[str]) -> bool:
    source = row.get("reactions", "")
    if arena_neutral_reaction_source(source):
        return True
    if reactions == ["Parry"]:
        return parse_parry_ac_bonus(source) is not None
    if reactions == ["Redirect Attack"]:
        return parse_redirect_attack_range(source) == 5
    return not reactions


def _unmodeled_action_rider(actions: str) -> bool:
    sanitized = _SUPPORTED_BLOODIED_REPLACEMENT.sub("damage", actions)
    sanitized = _SUPPORTED_FIXED_ON_HIT.sub("damage", sanitized)
    return bool(_HIDDEN_RIDER.search(sanitized))


def _limited_use_relevant(row: dict[str, object]) -> bool:
    return any(limited_use_source_relevant(row, name) for name in parse_limited_use_names(row))


def _source_blockers(row: dict[str, object], monster_names: set[str]) -> list[str]:
    blockers: list[str] = []
    try:
        relevant_traits = combat_relevant_trait_names(row.get("traits", ""))
        if any(name not in _ALLOWED_TRAITS for name in relevant_traits):
            blockers.append("trait")
    except ValueError:
        blockers.append("trait-parse")
    try:
        reactions = parse_reaction_names(row.get("reactions", ""))
        if not _reaction_is_modeled(row, reactions):
            blockers.append("reaction")
    except ValueError:
        blockers.append("reaction-parse")
    try:
        if not arena_neutral_bonus_action_source(row.get("bonusActions", "")):
            blockers.append("bonus-action")
    except ValueError:
        blockers.append("bonus-action-parse")
    try:
        if _limited_use_relevant(row):
            blockers.append("limited-use")
    except ValueError:
        blockers.append("limited-use-parse")
    try:
        if legendary_source_relevant(row.get("legendaryActions", "")):
            blockers.append("legendary")
    except ValueError:
        blockers.append("legendary-parse")
    if spellcasting_fingerprint(row) is not None and not arena_neutral_spellcasting(row):
        blockers.append("spellcasting")
    try:
        parse_defense_profile(row)
    except ValueError:
        blockers.append("defense-clause")
    actions = str(row.get("actions", ""))
    if combat_math_relevant(actions) and not _ATTACK_ROLL.search(actions):
        blockers.append("no-attack-roll")
    if _COMPLEX_ACTION.search(actions):
        blockers.append("save-or-complex-action")
    if _CONDITION_OR_CONTROL.search(actions):
        blockers.append("condition-or-control")
    if _unmodeled_action_rider(actions):
        blockers.append("unsupported-action-rider")
    if _has_neighbor_bleed(row, monster_names):
        blockers.append("source-neighbor-bleed")
    if not blockers and not _ATTACK_ROLL.search(actions):
        blockers.append(_NONCOMBAT)
    return blockers


def _ready_names() -> set[str]:
    return {card.name for card in build_monster_catalog() if card.coverage_status is CoverageStatus.RAW_READY}


def main() -> None:
    rows = load_monster_rows()
    monster_names = {str(row["name"]) for row in rows}
    ready_names = _ready_names()
    safe: list[dict[str, object]] = []
    already_ready: list[str] = []
    deferred: list[str] = []
    noncombat: list[str] = []
    blocker_counts: dict[str, int] = {}
    blocker_names: dict[str, list[str]] = {}
    reaction_details: list[dict[str, object]] = []
    rider_details: list[dict[str, object]] = []
    for row in rows:
        name = str(row["name"])
        if name in ready_names:
            already_ready.append(name)
            continue
        if deferred_environment_reason(row["speed"]) is not None:
            deferred.append(name)
            continue
        blockers = _source_blockers(row, monster_names)
        if blockers == [_NONCOMBAT]:
            noncombat.append(name)
            continue
        for blocker in set(blockers):
            blocker_counts[blocker] = blocker_counts.get(blocker, 0) + 1
            blocker_names.setdefault(blocker, []).append(name)
        if "reaction" in blockers:
            reaction_details.append({"name": name, "blockers": blockers, "reactions": str(row.get("reactions", ""))})
        if "unsupported-action-rider" in blockers:
            rider_details.append({"name": name, "blockers": blockers, "actions": str(row.get("actions", ""))})
        if not blockers:
            safe.append(row)
    print(
        f"ZERO_ENGINE_BASELINE existing={len(already_ready)} missing={len(safe)} "
        f"deferred={len(deferred)} noncombat={len(noncombat)}"
    )
    if deferred:
        print("ZERO_ENGINE_DEFERRED_ENVIRONMENT\t" + " | ".join(sorted(deferred)))
    if noncombat:
        print("ZERO_ENGINE_DEFERRED_NONCOMBAT\t" + " | ".join(sorted(noncombat)))
    for row in safe:
        detail = {field: row.get(field, "") for field in _DETAIL_FIELDS}
        raw = str(row.get("rawText", ""))
        initiative = re.search(r"\bInitiative\s+([+-]?\d+)", raw, re.I)
        detail["initiative"] = int(initiative.group(1)) if initiative else None
        print("ZERO_ENGINE_DETAIL\t" + json.dumps(detail, ensure_ascii=False, separators=(",", ":")))
    for detail in reaction_details:
        print("ZERO_ENGINE_REACTION_DETAIL\t" + json.dumps(detail, ensure_ascii=False, separators=(",", ":")))
    for detail in rider_details:
        print("ZERO_ENGINE_RIDER_DETAIL\t" + json.dumps(detail, ensure_ascii=False, separators=(",", ":")))
    for blocker, count in sorted(blocker_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"ZERO_ENGINE_BLOCKER\t{blocker}\t{count}")
        if count <= _DETAIL_BLOCKER_LIMIT:
            print(f"ZERO_ENGINE_BLOCKER_NAMES\t{blocker}\t" + " | ".join(sorted(blocker_names[blocker])))


if __name__ == "__main__":
    main()
