from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from app.content.canonical_pregen_mechanics import derive_canonical_pregen_mechanics
from app.content.monster_catalog import load_monster_rows
from app.content.monster_trait_source_audit import parse_trait_names


@dataclass(frozen=True)
class MechanicFamily:
    id: str
    monster_names: tuple[str, ...]

    @property
    def demand_count(self) -> int:
        return len(self.monster_names)


_ACTION_PATTERNS = {
    "recharge": re.compile(r"\bRecharge\s+\d(?:\s*[-–]\s*\d)?\b", re.I),
    "saving-throw-action": re.compile(r"\bSaving Throw:\s*DC\s*\d+\b", re.I),
    "on-hit-grapple": re.compile(r"\bHit:.*\bGrappled condition\b", re.I),
    "on-hit-prone": re.compile(r"\bHit:.*\bProne condition\b", re.I),
    "on-hit-poisoned": re.compile(r"\bHit:.*\bPoisoned condition\b", re.I),
    "attachment": re.compile(r"\battach(?:es|ed)?\b", re.I),
    "recurring-turn-damage": re.compile(r"\btakes?\s+\d+\s*\([^)]*\)\s+\w+\s+damage\s+at\s+the\s+(?:start|end)\s+of\b", re.I),
    "next-attack-advantage": re.compile(r"\bAdvantage on the next attack roll\b|\bnext attack roll[^.]*Advantage\b", re.I),
    "next-attack-disadvantage": re.compile(r"\bDisadvantage on the next attack roll\b|\bnext attack roll[^.]*Disadvantage\b", re.I),
    "injured-target-advantage": re.compile(
        r"\bAdvantage\b[^.]*\btarget\b[^.]*\bdoesn[’']t have all (?:of )?its Hit Points\b",
        re.I,
    ),
    "hit-point-maximum-reduction": re.compile(r"\bHit Point maximum\s+(?:decreases|is reduced)\b", re.I),
    "damage-reduction": re.compile(r"\breduces?\s+the\s+damage\b", re.I),
    "multiattack": re.compile(r"\bMultiattack\.\b", re.I),
}

_TRAIT_FAMILIES = {
    "Pack Tactics": "pack-tactics",
    "Blood Frenzy": "injured-target-advantage",
    "Regeneration": "regeneration",
    "Undead Fortitude": "undead-fortitude",
    "Magic Resistance": "magic-resistance",
    "Swarm": "swarm",
}


def build_monster_mechanic_families() -> tuple[MechanicFamily, ...]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for row in load_monster_rows():
        name = str(row["name"])
        actions = str(row.get("actions", ""))
        for family_id, pattern in _ACTION_PATTERNS.items():
            if pattern.search(actions):
                grouped[family_id].add(name)
        for trait in parse_trait_names(row.get("traits", "")):
            family_id = _TRAIT_FAMILIES.get(trait)
            if family_id:
                grouped[family_id].add(name)
        if str(row.get("bonusActions", "")).strip():
            grouped["bonus-action"].add(name)
        if str(row.get("reactions", "")).strip():
            grouped["reaction"].add(name)
        if str(row.get("legendaryActions", "")).strip():
            grouped["legendary-action"].add(name)
        if "Spellcasting." in actions:
            grouped["spellcasting"].add(name)
    return tuple(
        MechanicFamily(family_id, tuple(sorted(names)))
        for family_id, names in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    )


def build_hero_mechanic_demand() -> dict[str, tuple[str, ...]]:
    return {
        item.id: item.owners
        for item in derive_canonical_pregen_mechanics()
    }
