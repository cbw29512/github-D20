from __future__ import annotations

from app.content.monster_catalog import build_monster_catalog, load_monster_rows
from app.content.monster_trait_source_audit import parse_trait_names, trait_issues
from app.content.roster import build_arena_roster
from app.domain.catalog import CoverageStatus
from app.domain.traits import CombatTrait


def _row(name: str) -> dict[str, object]:
    return next(row for row in load_monster_rows() if row["name"] == name)


def _monster(name: str):
    return next(monster for monster in build_arena_roster().monsters if monster.name == name)


def test_trait_parser_preserves_multiple_printed_headings() -> None:
    assert parse_trait_names(
        "Pack Tactics. The wolf has Advantage on attack rolls. Sunlight Sensitivity. While in sunlight, it has Disadvantage."
    ) == ["Pack Tactics", "Sunlight Sensitivity"]


def test_trait_parser_normalizes_parenthetical_usage_with_internal_punctuation() -> None:
    assert parse_trait_names(
        "Amphibious. Legendary Resistance (3/Day, or 4/Day in Lair). The dragon can choose to succeed instead."
    ) == ["Amphibious", "Legendary Resistance"]


def test_shared_heading_parser_can_preserve_printed_annotations() -> None:
    assert parse_trait_names("Rampage (1/Day). The gnoll moves and attacks.", preserve_annotations=True) == [
        "Rampage (1/Day)"
    ]


def test_wolf_pack_tactics_is_source_derived_and_runtime_backed() -> None:
    wolf = _monster("Wolf")
    assert wolf.source_trait_names == ["Pack Tactics"]
    assert CombatTrait.PACK_TACTICS in wolf.combat_traits
    assert trait_issues(wolf, _row("Wolf")) == []


def test_arena_neutral_trait_remains_fingerprinted() -> None:
    deer = _monster("Deer")
    assert deer.source_trait_names == ["Agile"]
    assert trait_issues(deer, _row("Deer")) == []


def test_unknown_outcome_changing_trait_fails_closed() -> None:
    wolf = _monster("Wolf")
    row = dict(_row("Wolf"))
    row["traits"] = "Magic Resistance. The wolf has Advantage on saving throws against spells and magical effects."
    drifted = wolf.model_copy(update={"source_trait_names": ["Magic Resistance"], "combat_traits": []})
    assert "uncertified-trait:magic-resistance" in trait_issues(drifted, row)


def test_catalog_blocks_missing_runtime_pack_tactics(monkeypatch) -> None:
    roster = build_arena_roster()
    monsters = [
        monster.model_copy(update={"combat_traits": []}) if monster.name == "Wolf" else monster
        for monster in roster.monsters
    ]
    monkeypatch.setattr(
        "app.content.roster.build_arena_roster",
        lambda: roster.model_copy(update={"monsters": monsters}),
    )
    card = next(item for item in build_monster_catalog() if item.name == "Wolf")
    assert card.coverage_status is CoverageStatus.BLOCKED
    assert card.runnable_template_id is None
    assert "trait-runtime-missing:pack-tactics" in card.blockers
