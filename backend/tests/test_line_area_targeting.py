from app.combat.save_area_targeting import area_targets
from app.combat.state import build_combatant_state
from app.content.audited_fighter import build_karnok_stoneward
from app.content.capability_registry import build_combatant_from_capabilities
from app.domain.encounters import EncounterCombatant, EncounterSetup


def _member(template, side: str, index: int, position: int) -> EncounterCombatant:
    return EncounterCombatant(
        combatant_id=f"{side}-{index}:{template.id}", side=side, position_ft=position,
        state=build_combatant_state(template),
    )


def _line_setup() -> tuple[EncounterCombatant, EncounterSetup]:
    dragon = build_combatant_from_capabilities("srd-young-black-dragon")
    hero = build_karnok_stoneward()
    monsters = [_member(dragon, "monsters", index, 15) for index in range(3)]
    heroes = [_member(hero, "heroes", index, 5) for index in range(6)]
    return monsters[1], EncounterSetup(
        heroes=heroes, monsters=monsters, hero_total_levels=6,
        monster_total_cr="21", starting_distance_ft=10,
    )


def test_five_foot_line_stays_in_actors_three_by_two_column() -> None:
    actor, setup = _line_setup()
    targets = area_targets(actor, setup, actor.state.template.saving_throw_actions[0])
    assert [setup.heroes.index(target) for target in targets] == [1, 4]


def test_line_does_not_slide_to_a_better_neighboring_column() -> None:
    actor, setup = _line_setup()
    for index in (1, 4):
        setup.heroes[index].state.current_hp = 0
        setup.heroes[index].state.is_alive = False
        setup.heroes[index].state.is_dead = True
    assert area_targets(actor, setup, actor.state.template.saving_throw_actions[0]) == []


def test_living_ally_ahead_blocks_same_column_line() -> None:
    actor, setup = _line_setup()
    setup.monsters.extend([
        _member(actor.state.template, "monsters", 3, 15),
        _member(actor.state.template, "monsters", 4, 10),
    ])
    assert area_targets(actor, setup, actor.state.template.saving_throw_actions[0]) == []
