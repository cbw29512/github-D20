from app.combat.dice import FixedDiceProvider
from app.combat.encounter_combat_turn import resolve_combat_turn
from app.combat.encounter_setup import build_encounter_setup
from app.combat.save_action_turn import resolve_save_action_turn
from app.domain.actions import AttackActionDefinition, AttackActionSlot, SavingThrowAction
from app.domain.areas import AreaGeometry
from app.domain.models import EncounterSelection
from app.domain.runtime import ResourceState


def _breath() -> SavingThrowAction:
    return SavingThrowAction(
        id="test-breath", name="Test Breath", save_ability="constitution", dc=11,
        range_ft=15, area=AreaGeometry(shape="cone", size_ft=15),
        damage_dice_count=6, damage_dice_size=6, damage_type="poison",
        success_damage="half", resource_id="test-breath", resource_cost=1,
    )


def _give_breath(actor) -> None:
    actor.state.template.saving_throw_actions = [_breath()]
    actor.state.resources = [ResourceState(id="test-breath", name="Test Breath", current_uses=1, max_uses=1)]


def test_cone_hits_multiple_targets_with_one_shared_damage_roll_and_resource_spend() -> None:
    setup = build_encounter_setup(EncounterSelection(
        hero_ids=["karnok-stoneward-l1", "mara-quickstep-l1", "rokhan-stonefury-l1"],
        monster_ids=["srd-commoner"],
    ))
    actor = setup.monsters[0]
    actor.position_ft = 10
    for hero in setup.heroes:
        hero.position_ft = 5
    _give_breath(actor)

    events, _, used = resolve_save_action_turn(
        1, 1, actor, setup, FixedDiceProvider([1, 1, 2, 3, 4, 5, 6, 1, 1]),
        resource_backed_only=True,
    )

    assert used is True
    assert len(events) == 3
    assert len({event.target_id for event in events}) == 3
    assert all(event.damage_roll is not None for event in events)
    assert all(event.damage_roll.rolls == [1, 2, 3, 4, 5, 6] for event in events)
    assert actor.state.resources[0].current_uses == 0
    assert actor.state.action_available is False


def test_resource_backed_save_offense_precedes_multiattack() -> None:
    setup = build_encounter_setup(EncounterSelection(
        hero_ids=["karnok-stoneward-l1"], monster_ids=["srd-commoner"],
    ))
    hero, actor = setup.heroes[0], setup.monsters[0]
    _give_breath(actor)
    attack_id = actor.state.template.weapon_attack.id
    actor.state.template.attack_action = AttackActionDefinition(
        id="test-multiattack", name="Multiattack",
        slots=[AttackActionSlot(attack_ids=[attack_id]), AttackActionSlot(attack_ids=[attack_id])],
    )

    events, _ = resolve_combat_turn(
        1, 1, actor, hero, setup, FixedDiceProvider([1, 1, 2, 3, 4, 5, 6]),
    )

    assert any(event.feature_id == "test-breath" for event in events)
    assert not any(event.event_type == "attack" for event in events)
    assert actor.state.resources[0].current_uses == 0
