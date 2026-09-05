from app.content.monster_catalog import load_monster_rows
from app.content.monster_spellcasting_source_audit import (
    arena_neutral_spellcasting,
    printed_spell_names,
    spellcasting_fingerprint,
    spellcasting_issues,
)
from app.content.roster import build_arena_roster


def _row(name: str) -> dict[str, object]:
    return next(row for row in load_monster_rows() if row["name"] == name)


def _monster(name: str):
    return next(template for template in build_arena_roster().monsters if template.name == name)


def test_giant_owl_divinations_are_explicitly_arena_neutral() -> None:
    row = _row("Giant Owl")
    template = _monster("Giant Owl")

    assert arena_neutral_spellcasting(row)
    assert spellcasting_issues(template, row) == []


def test_combat_spell_added_to_neutral_caster_fails_closed() -> None:
    row = dict(_row("Giant Owl"))
    row["actions"] = str(row["actions"]).replace(
        "1/Day: Clairvoyance",
        "1/Day: Clairvoyance, Fireball",
    )
    template = _monster("Giant Owl").model_copy(
        update={"source_spellcasting_fingerprint": spellcasting_fingerprint(row)}
    )

    assert not arena_neutral_spellcasting(row)
    issues = spellcasting_issues(template, row)
    assert "uncertified-monster-spellcasting" in issues
    assert "spell-concentration-source-not-vendored" in issues


def test_shapechange_parenthetical_commas_stay_inside_one_spell_entry() -> None:
    spells = printed_spell_names(_row("Adult Gold Dragon"))

    shapechange = [spell for spell in spells if spell.startswith("Shapechange (")]
    assert len(shapechange) == 1
    assert "no Temporary Hit Points gained from the spell" in shapechange[0]
    assert not any(spell.startswith("no ") for spell in spells)


def test_spell_list_stops_before_following_gold_dragon_breath_feature() -> None:
    spells = printed_spell_names(_row("Adult Gold Dragon"))

    assert "Zone of Truth" in spells
    assert not any("Weakening Breath" in spell for spell in spells)
    assert not any("Saving Throw" in spell for spell in spells)
