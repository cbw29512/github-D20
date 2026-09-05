from app.content.monster_catalog import build_monster_catalog, load_monster_rows
from app.content.monster_defense_source_audit import parse_defense_profile
from app.content.monster_source_audit import audit_monster_source
from app.content.roster import build_arena_roster
from app.domain.catalog import CoverageStatus


def _rows_by_name() -> dict[str, dict[str, object]]:
    return {str(row["name"]): row for row in load_monster_rows()}


def test_every_raw_ready_monster_reconciles_to_srd_5_2_1_source() -> None:
    rows = _rows_by_name()
    runtime = {template.id: template for template in build_arena_roster().monsters}
    ready = [card for card in build_monster_catalog() if card.coverage_status is CoverageStatus.RAW_READY]
    mismatches: list[str] = []
    for card in ready:
        if card.runnable_template_id not in runtime:
            mismatches.append(f"{card.name}: missing-runtime-template")
            continue
        issues = audit_monster_source(runtime[card.runnable_template_id], rows[card.name])
        if issues:
            mismatches.append(f"{card.name} ({card.source_reference}): {', '.join(issues)}")
    assert mismatches == [], "RAW-ready monster source mismatches:\n" + "\n".join(mismatches)


def test_source_audit_detects_an_omitted_printed_attack() -> None:
    rows = _rows_by_name()
    bear = next(template for template in build_arena_roster().monsters if template.name == "Brown Bear").model_copy(deep=True)
    assert len(bear.alternate_weapon_attacks) == 1
    bear.alternate_weapon_attacks = []
    assert "source-attack-count-mismatch" in audit_monster_source(bear, rows["Brown Bear"])


def test_source_audit_intentionally_ignores_movement_rate_drift() -> None:
    rows = _rows_by_name()
    bat = next(template for template in build_arena_roster().monsters if template.name == "Bat").model_copy(deep=True)
    assert bat.movement_modes.fly_ft == 30
    bat.movement_modes.fly_ft = 0
    assert audit_monster_source(bat, rows["Bat"]) == []


def test_catalog_does_not_block_raw_ready_for_movement_rate_drift(monkeypatch) -> None:
    roster = build_arena_roster()
    bat = next(template for template in roster.monsters if template.name == "Bat")
    bat.movement_modes.fly_ft = 0
    monkeypatch.setattr("app.content.roster.build_arena_roster", lambda: roster)
    card = next(item for item in build_monster_catalog() if item.name == "Bat")
    assert card.coverage_status is CoverageStatus.RAW_READY
    assert card.runnable_template_id == "srd-bat"
    assert card.blockers == []


def test_catalog_blocks_raw_ready_when_any_source_stat_drifts(monkeypatch) -> None:
    roster = build_arena_roster()
    guard = next(template for template in roster.monsters if template.name == "Guard")
    guard.armor_class += 1
    monkeypatch.setattr("app.content.roster.build_arena_roster", lambda: roster)
    card = next(item for item in build_monster_catalog() if item.name == "Guard")
    assert card.coverage_status is CoverageStatus.BLOCKED
    assert card.runnable_template_id is None
    assert "armor-class-mismatch" in card.blockers


def test_srd_defense_parser_distinguishes_damage_and_condition_defenses() -> None:
    rows = _rows_by_name()
    shrub = parse_defense_profile(rows["Awakened Shrub"])
    assert shrub["damage_vulnerabilities"] == {"fire"}
    assert shrub["damage_resistances"] == {"piercing"}
    assert shrub["damage_immunities"] == set()
    assert shrub["condition_immunities"] == set()
    skeleton = parse_defense_profile(rows["Skeleton"])
    assert skeleton["damage_vulnerabilities"] == {"bludgeoning"}
    assert skeleton["damage_immunities"] == {"poison"}
    assert skeleton["condition_immunities"] == {"exhaustion", "poisoned"}
    hydra = parse_defense_profile(rows["Hydra"])
    assert hydra["damage_immunities"] == set()
    assert hydra["condition_immunities"] == {"blinded", "charmed", "deafened", "frightened", "stunned", "unconscious"}
    elemental = parse_defense_profile(rows["Fire Elemental"])
    assert elemental["damage_resistances"] == {"bludgeoning", "piercing", "slashing"}
    assert elemental["damage_immunities"] == {"fire", "poison"}
    assert elemental["condition_immunities"] == {"exhaustion", "grappled", "paralyzed", "petrified", "poisoned", "prone", "restrained", "unconscious"}


def test_raw_ready_monsters_are_audited_runtime_subset() -> None:
    cards = build_monster_catalog()
    ready_ids = {card.runnable_template_id for card in cards if card.coverage_status is CoverageStatus.RAW_READY}
    runtime_ids = {template.id for template in build_arena_roster().monsters}
    assert ready_ids <= runtime_ids
    berserker = next(card for card in cards if card.name == "Berserker")
    assert berserker.runnable_template_id is None
    assert berserker.blockers == ["monster-combat-mechanics-not-certified"]


def test_raw_ready_monsters_have_precise_srd_page_references() -> None:
    for card in build_monster_catalog():
        if card.coverage_status is CoverageStatus.RAW_READY:
            assert card.source_reference == f"SRD 5.2.1 p. {card.source_page}"
