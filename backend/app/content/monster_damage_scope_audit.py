from __future__ import annotations

from dataclasses import dataclass
import re

from app.content.monster_spellcasting_source_audit import spellcasting_fingerprint

_DAMAGE = re.compile(r"\bdamage\b", re.I)
_ATTACK = re.compile(r"\b(?:Melee|Ranged|Melee or Ranged)\s+Attack Roll:", re.I)
_SAVE = re.compile(r"\bSaving Throw:", re.I)
_MULTIATTACK = re.compile(r"\bMultiattack\b", re.I)
_AREA = re.compile(r"\b(?:cone|line|sphere|radius|emanation|cube|cylinder)\b", re.I)
_LIMITED = re.compile(r"\b(?:Recharge\s*\d|\d+\s*/\s*Day|\d+\s+Uses?)\b", re.I)
_REPEATED = re.compile(r"\b(?:start|end) of (?:its|the target'?s|each) turn\b", re.I)
_HEALING = re.compile(r"\b(?:regains?\s+\d+|Temporary Hit Points?)\b", re.I)
_DEFENSE = re.compile(r"\b(?:Vulnerabilities|Resistances|Immunities)\b", re.I)
_EXTRA_DAMAGE = re.compile(r"\bplus\s+[^.]{0,80}\bdamage\b", re.I)
_FLAT_ROLL_MODIFIER = re.compile(
    r"\b(?:add(?:s)?|subtract(?:s)?)\s+[+-]?\d+\s+(?:to|from)\s+(?:the|that|its|their)?\s*"
    r"(?:roll|ability check|saving throw|attack roll)\b"
    r"|\b[+-]\d+\s+(?:bonus|penalty)\s+to\s+(?:an?|the|its|their)?\s*"
    r"(?:roll|ability check|saving throw|attack roll)\b",
    re.I,
)


@dataclass(frozen=True)
class MonsterDamageAudit:
    monster_id: str
    monster_name: str
    families: tuple[str, ...]


def _damaging(text: object) -> bool:
    return bool(_DAMAGE.search(str(text or "")))


def audit_monster_damage_scope(row: dict[str, object]) -> MonsterDamageAudit:
    actions = str(row.get("actions", ""))
    bonus = str(row.get("bonusActions", ""))
    reactions = str(row.get("reactions", ""))
    legendary = str(row.get("legendaryActions", ""))
    traits = str(row.get("traits", ""))
    raw = str(row.get("rawText", ""))
    all_combat = "\n".join((traits, actions, bonus, reactions, legendary))
    families: set[str] = set()

    if _ATTACK.search(actions) and _damaging(actions):
        families.add("attack-roll-damage")
    if _SAVE.search(actions) and _damaging(actions):
        families.add("save-damage")
    if _MULTIATTACK.search(actions) and _damaging(actions):
        families.add("multiattack-damage")
    if _EXTRA_DAMAGE.search(actions):
        families.add("typed-damage-rider")
    if _AREA.search(actions) and _damaging(actions):
        families.add("area-damage")
    if _LIMITED.search(all_combat) and _damaging(all_combat):
        families.add("limited-or-recharge-damage")
    if _REPEATED.search(all_combat) and _damaging(all_combat):
        families.add("persistent-damage")
    if _damaging(bonus):
        families.add("bonus-action-damage")
    if _damaging(reactions):
        families.add("reaction-damage")
    if _damaging(legendary):
        families.add("legendary-action-damage")
    if _FLAT_ROLL_MODIFIER.search(all_combat):
        families.add("flat-roll-modifier")
    if _HEALING.search(all_combat):
        families.add("healing-or-temporary-hp")
    if _DEFENSE.search(raw):
        families.add("damage-defense")
    if spellcasting_fingerprint(row) is not None:
        families.add("spellcasting-damage-candidate")

    return MonsterDamageAudit(
        monster_id=str(row["id"]),
        monster_name=str(row["name"]),
        families=tuple(sorted(families)),
    )
