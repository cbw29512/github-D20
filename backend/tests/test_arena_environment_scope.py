from app.content.arena_eligibility import deferred_environment_reason, standard_arena_eligible
from app.content.legacy_monster_roster import build_legacy_monster_templates
from app.content.monster_catalog import build_monster_catalog, load_monster_rows
from app.content.monsters_zero_engine import build_zero_engine_monsters
from app.domain.catalog import CoverageStatus
from app.domain.movement import MovementModes


def test_aquatic_only_killer_whale_is_deferred_from_standard_arena() -> None:
    templates = build_legacy_monster_templates()
    assert all(template.name != "Killer Whale" for template in templates)

    card = next(card for card in build_monster_catalog() if card.name == "Killer Whale")
    assert card.coverage_status is CoverageStatus.BLOCKED
    assert card.runnable_template_id is None
    assert card.blockers == ["deferred-environment:aquatic-only"]


def test_standard_arena_eligibility_defers_aquatic_only_by_mechanics_not_name() -> None:
    whale = next(template for template in build_zero_engine_monsters() if template.name == "Killer Whale")
    swimmer = whale.model_copy(update={"name": "Synthetic Swimmer", "movement_modes": MovementModes(walk_ft=0, swim_ft=40)})
    land_swimmer = whale.model_copy(update={"name": "Synthetic Land Swimmer", "movement_modes": MovementModes(walk_ft=30, swim_ft=40)})
    slow_land = whale.model_copy(update={"name": "Synthetic Slow Land Creature", "movement_modes": MovementModes(walk_ft=5)})
    flyer = whale.model_copy(update={"name": "Synthetic Flyer", "movement_modes": MovementModes(walk_ft=0, fly_ft=40)})
    immobile = whale.model_copy(update={"name": "Synthetic MV0 Creature", "movement_modes": MovementModes(walk_ft=0)})

    assert deferred_environment_reason(swimmer.movement_modes) == "aquatic-only"
    assert standard_arena_eligible(swimmer) is False
    assert deferred_environment_reason(land_swimmer.movement_modes) is None
    assert standard_arena_eligible(land_swimmer) is True
    assert standard_arena_eligible(slow_land) is True
    assert standard_arena_eligible(flyer) is True
    assert standard_arena_eligible(immobile) is False


def test_srd_catalog_has_nine_aquatic_only_environment_deferrals() -> None:
    deferred = {
        str(row["name"])
        for row in load_monster_rows()
        if deferred_environment_reason(row["speed"]) == "aquatic-only"
    }

    assert len(deferred) == 9


def test_land_arena_grapple_batch_remains_eligible() -> None:
    names = {template.name for template in build_legacy_monster_templates()}
    assert {"Giant Scorpion", "Grick", "Griffon"} <= names
