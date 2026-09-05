from __future__ import annotations

import pytest

from app.content.monster_catalog import load_monster_rows
from app.content.monster_reaction_source_audit import (
    arena_neutral_reaction_source,
    parse_parry_ac_bonus,
    parse_reaction_names,
    parse_redirect_attack_range,
    reaction_issues,
)
from app.content.roster import build_arena_roster
from app.domain.reactions import ParryReaction, RedirectAttackReaction


def _row(name: str) -> dict[str, object]:
    return next(row for row in load_monster_rows() if row["name"] == name)


def _monster(name: str):
    return next(monster for monster in build_arena_roster().monsters if monster.name == name)


def test_reaction_parser_reads_real_srd_trigger_response_heading() -> None:
    assert parse_reaction_names(_row("Rust Monster")["reactions"]) == ["Reflexive Antennae"]


def test_reaction_parser_reads_real_srd_spell_trigger_headings() -> None:
    for name in ("Archmage", "Lich", "Mage"):
        assert parse_reaction_names(_row(name)["reactions"]) == [
            "Protective Magic" if name == "Lich" else "Protective Magic (3/Day)"
        ]


def test_reaction_parser_preserves_multiple_headings() -> None:
    source = (
        "Parry. Trigger: An attack roll hits. Response: The creature gains AC. "
        "Riposte. Trigger: An attack roll misses. Response: The creature attacks."
    )
    assert parse_reaction_names(source) == ["Parry", "Riposte"]


def test_reaction_parser_still_fails_closed_on_unknown_prose_shape() -> None:
    with pytest.raises(ValueError, match="could not be parsed"):
        parse_reaction_names("Unclear Defense. The creature does something reactive.")


def test_standard_parry_bonus_is_source_derived() -> None:
    assert parse_parry_ac_bonus(_row("Bandit Captain")["reactions"]) == 2
    assert parse_parry_ac_bonus(_row("Gladiator")["reactions"]) == 3


def test_exact_standard_parry_can_be_certified() -> None:
    template = _monster("Wolf").model_copy(update={
        "source_reaction_names": ["Parry"],
        "parry_reaction": ParryReaction(ac_bonus=2),
    })
    assert reaction_issues(template, _row("Bandit Captain")) == []


def test_wrong_parry_bonus_still_fails_closed() -> None:
    template = _monster("Wolf").model_copy(update={
        "source_reaction_names": ["Parry"],
        "parry_reaction": ParryReaction(ac_bonus=3),
    })
    issues = reaction_issues(template, _row("Bandit Captain"))
    assert "parry-source-mismatch" in issues
    assert "uncertified-reaction:parry" in issues


def test_exact_redirect_attack_can_be_certified() -> None:
    boss = _monster("Goblin Boss")
    assert parse_redirect_attack_range(_row("Goblin Boss")["reactions"]) == 5
    assert boss.source_reaction_names == ["Redirect Attack"]
    assert reaction_issues(boss, _row("Goblin Boss")) == []


def test_redirect_attack_range_drift_fails_closed() -> None:
    boss = _monster("Goblin Boss").model_copy(update={
        "redirect_attack_reaction": RedirectAttackReaction(ally_range_ft=10),
    })
    issues = reaction_issues(boss, _row("Goblin Boss"))
    assert "redirect-attack-source-mismatch" in issues
    assert "uncertified-reaction:redirect-attack" in issues


def test_empty_reaction_fingerprint_is_source_derived() -> None:
    saber = _monster("Saber-Toothed Tiger")
    assert saber.source_reaction_names == []
    assert reaction_issues(saber, _row("Saber-Toothed Tiger")) == []


def test_nonstandard_parry_prose_still_fails_closed() -> None:
    wolf = _monster("Wolf")
    row = dict(_row("Wolf"))
    row["reactions"] = "Parry. Trigger: An attack roll hits. Response: The wolf gains +2 AC."
    drifted = wolf.model_copy(update={"source_reaction_names": ["Parry"]})
    issues = reaction_issues(drifted, row)
    assert "parry-source-mismatch" in issues
    assert "uncertified-reaction:parry" in issues


def test_spell_trigger_reaction_remains_uncertified_until_runtime_semantics_exist() -> None:
    mage = _monster("Wolf").model_copy(update={"source_reaction_names": ["Protective Magic (3/Day)"]})
    assert "uncertified-reaction:protective-magic-3-day" in reaction_issues(mage, _row("Mage"))


def test_reaction_fingerprint_drift_is_detected() -> None:
    wolf = _monster("Wolf").model_copy(update={"source_reaction_names": ["Parry"]})
    assert "source-reaction-fingerprint-mismatch" in reaction_issues(wolf, _row("Wolf"))


def test_shrieker_audible_only_reaction_is_arena_neutral() -> None:
    source = _row("Shrieker Fungus")["reactions"]

    assert "until the shrieker dies" in str(source)
    assert arena_neutral_reaction_source(source)


def test_audible_reaction_with_combat_math_still_fails_closed() -> None:
    source = (
        "Alarm. Trigger: A creature moves within 30 feet of the monster. "
        "Response: The monster emits a shriek audible within 300 feet of itself "
        "for 1 minute or until the monster dies. The triggering creature takes 1 Psychic damage."
    )

    assert not arena_neutral_reaction_source(source)
