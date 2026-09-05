from __future__ import annotations

import logging
import re
from functools import lru_cache

from app.content.monster_combat_scope import combat_math_relevant, feature_blocks
from app.content.monster_catalog import load_monster_rows
from app.domain.models import CombatantTemplate

logger = logging.getLogger(__name__)
_TRIGGER_RESPONSE_HEADING = re.compile(r"(?:^|(?<=\.\s))([^.]{1,80})\.\s+Trigger:\s", re.MULTILINE)
_SPELL_TRIGGER_HEADING = re.compile(
    r"(?:^|(?<=\.\s))([^.]{1,80})\.\s+"
    r"(?=[^.]{1,300}\bcasts?\b[^.]{0,200}\bin response to\b[^.]{0,100}\btrigger\b)",
    re.IGNORECASE | re.MULTILINE,
)
_PARRY = re.compile(
    r"\bParry\.\s+Trigger:\s+The [^.]+ is hit by a melee attack roll while holding a weapon\.\s+"
    r"Response:\s+The [^.]+ adds (?P<bonus>\d+) to its AC against that attack, possibly causing it to miss\.",
    re.IGNORECASE,
)
_REDIRECT_ATTACK = re.compile(
    r"\bRedirect Attack\.\s+Trigger:\s+A creature the goblin can see makes an attack roll against it\.\s+"
    r"Response:\s+The goblin chooses a Small or Medium ally within (?P<range>\d+) feet of itself\.\s+"
    r"The goblin and that ally swap places, and the ally becomes the target of the attack instead\.",
    re.IGNORECASE,
)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _reaction_heading_matches(text: str) -> list[tuple[int, str]]:
    matches = [
        (match.start(1), match.group(1).strip())
        for pattern in (_TRIGGER_RESPONSE_HEADING, _SPELL_TRIGGER_HEADING)
        for match in pattern.finditer(text)
    ]
    return sorted(set(matches), key=lambda item: item[0])


def parse_reaction_names(source_reactions: object) -> list[str]:
    """Extract named SRD reactions from reviewed 2024 reaction prose shapes."""
    text = str(source_reactions or "").strip()
    if not text:
        return []
    names = [name for _, name in _reaction_heading_matches(text)]
    if not names:
        raise ValueError(f"SRD reaction headings could not be parsed from: {text!r}")
    return names


def arena_neutral_reaction_source(source_reactions: object) -> bool:
    """True when every printed reaction is movement/sensory/presentation-only in Iron Pit."""
    names = parse_reaction_names(source_reactions)
    if not names:
        return True
    blocks = feature_blocks(source_reactions, names)
    return all(not combat_math_relevant(blocks[name]) for name in names)


def parse_parry_ac_bonus(source_reactions: object) -> int | None:
    match = _PARRY.search(str(source_reactions or ""))
    return int(match.group("bonus")) if match else None


def parse_redirect_attack_range(source_reactions: object) -> int | None:
    match = _REDIRECT_ATTACK.search(str(source_reactions or ""))
    return int(match.group("range")) if match else None


def _parry_matches(template: CombatantTemplate, source: object) -> bool:
    bonus = parse_parry_ac_bonus(source)
    return bonus is not None and template.parry_reaction is not None and template.parry_reaction.ac_bonus == bonus


def _redirect_matches(template: CombatantTemplate, source: object) -> bool:
    ally_range = parse_redirect_attack_range(source)
    reaction = template.redirect_attack_reaction
    return bool(ally_range is not None and reaction is not None and reaction.ally_range_ft == ally_range
                and reaction.ally_max_size.value == "medium")


def reaction_issues(template: CombatantTemplate, row: dict[str, object]) -> list[str]:
    """Certify outcome-changing reactions; ignore reaction text outside Iron Pit combat scope."""
    source = row.get("reactions", "")
    expected = parse_reaction_names(source)
    issues: list[str] = []
    if template.source_reaction_names != expected:
        issues.append("source-reaction-fingerprint-mismatch")
    if template.parry_reaction is not None and "Parry" not in expected:
        issues.append("unexpected-parry-reaction")
    if template.redirect_attack_reaction is not None and "Redirect Attack" not in expected:
        issues.append("unexpected-redirect-attack-reaction")
    if not expected:
        return issues
    blocks = feature_blocks(source, expected)
    for name in expected:
        if name == "Parry" and _parry_matches(template, source):
            continue
        if name == "Redirect Attack" and _redirect_matches(template, source):
            continue
        if not combat_math_relevant(blocks[name]):
            continue
        if name == "Parry":
            issues.append("parry-source-mismatch")
        elif name == "Redirect Attack":
            issues.append("redirect-attack-source-mismatch")
        issues.append(f"uncertified-reaction:{_slug(name)}")
    return issues


@lru_cache(maxsize=1)
def _rows_by_name() -> dict[str, dict[str, object]]:
    return {str(row["name"]): row for row in load_monster_rows()}


def source_reaction_names(name: str) -> list[str]:
    row = _rows_by_name().get(name)
    if row is None:
        raise ValueError(f"No SRD 5.2.1 source row for monster {name!r}.")
    return parse_reaction_names(row.get("reactions", ""))


def complete_monster_reaction_fingerprints(templates: list[CombatantTemplate]) -> list[CombatantTemplate]:
    try:
        return [
            template.model_copy(update={"source_reaction_names": source_reaction_names(template.name)})
            if template.kind == "monster" else template
            for template in templates
        ]
    except Exception:
        logger.exception("Failed to derive canonical monster reaction fingerprints from SRD source.")
        raise
