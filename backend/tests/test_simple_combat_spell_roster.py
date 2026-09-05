from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROSTER = ROOT / "data" / "simple_combat_spell_roster_v1.json"
FULL_CASTERS = {"bard", "cleric", "druid", "sorcerer", "wizard"}
HALF_CASTERS = {"paladin", "ranger"}
WARLOCK_LEVELS = {str(level) for level in range(1, 10)}


def _payload() -> dict[str, object]:
    return json.loads(ROSTER.read_text(encoding="utf-8"))


def _assert_unique_spells(entry: dict[str, object]) -> None:
    levels = entry["levels"]
    flattened = [spell for spells in levels.values() for spell in spells]
    assert len(flattened) == len(set(flattened))


def test_full_casters_match_level20_slot_shape_with_distinct_spells() -> None:
    payload = _payload()
    expected = payload["full_caster_slot_shape"]
    for class_id in FULL_CASTERS:
        entry = payload["classes"][class_id]
        assert {level: len(spells) for level, spells in entry["levels"].items()} == expected
        assert sum(len(spells) for spells in entry["levels"].values()) == 22
        assert entry["cantrips"]
        _assert_unique_spells(entry)


def test_half_casters_match_level20_slot_shape_without_fake_cantrips() -> None:
    payload = _payload()
    expected = payload["half_caster_slot_shape"]
    for class_id in HALF_CASTERS:
        entry = payload["classes"][class_id]
        assert {level: len(spells) for level, spells in entry["levels"].items()} == expected
        assert sum(len(spells) for spells in entry["levels"].values()) == 15
        assert entry["cantrips"] == []
        _assert_unique_spells(entry)


def test_warlock_keeps_pact_choices_and_one_mystic_arcanum_each() -> None:
    entry = _payload()["classes"]["warlock"]
    assert set(entry["levels"]) == WARLOCK_LEVELS
    assert all(len(entry["levels"][str(level)]) == 3 for level in range(1, 6))
    assert all(len(entry["levels"][str(level)]) == 1 for level in range(6, 10))
    assert "eldritch-blast" in entry["cantrips"]
    _assert_unique_spells(entry)


def test_arcane_rosters_maximize_simple_spell_reuse() -> None:
    classes = _payload()["classes"]
    sorcerer = classes["sorcerer"]["levels"]
    wizard = classes["wizard"]["levels"]
    assert "magic-missile" in sorcerer["1"] and "magic-missile" in wizard["1"]
    assert "fireball" in sorcerer["3"] and "fireball" in wizard["3"]
    assert "blight" in sorcerer["4"] and "blight" in wizard["4"]
    assert "cone-of-cold" in sorcerer["5"] and "cone-of-cold" in wizard["5"]


def test_complex_spells_are_explicitly_deferred() -> None:
    deferred = set(_payload()["defer_complex_examples"])
    assert {"animate-objects", "simulacrum", "true-polymorph", "wish"} <= deferred
