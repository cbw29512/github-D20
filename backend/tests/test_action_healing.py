import pytest

from app.combat.action_economy import is_available, spend
from app.combat.charge import resolve_charge_closing
from app.combat.dice import FixedDiceProvider
from app.combat.encounter_setup import build_encounter_setup
from app.combat.healing import choose_healing_action, choose_healing_target, resolve_healing
from app.combat.state import begin_turn
from app.combat.zero_hp import apply_damage
from app.content.healing_spell_effects import build_heal
from app.domain.models import EncounterSelection, HealingAction


def _setup():
    return build_encounter_setup(EncounterSelection(
        hero_ids=["karnok-stoneward-l1", "rokhan-stonefury-l1"],
        monster_ids=["srd-goblin-warrior"],
    ))


def test_reaction_spends_once_and_refreshes_at_start_of_next_turn() -> None:
    state = _setup().heroes[0].state
    assert is_available(state, "reaction")
    spend(state, "reaction")
    assert not is_available(state, "reaction")
    with pytest.raises(ValueError):
        spend(state, "reaction")
    begin_turn(state)
    assert is_available(state, "reaction")


def test_incapacitated_creature_cannot_spend_action_bonus_action_or_reaction() -> None:
    state = _setup().heroes[0].state
    state.active_effect_ids.append("incapacitated")
    for cost in ("action", "bonus_action", "reaction"):
        assert not is_available(state, cost)
        with pytest.raises(ValueError):
            spend(state, cost)


def test_bonus_action_heal_rescues_downed_ally_before_self_and_preserves_action() -> None:
    setup = _setup()
    healer, ally = setup.heroes
    healer.state.current_hp = healer.state.template.max_hp // 2
    relentless = next(item for item in ally.state.resources if item.id == "relentless-endurance")
    relentless.current_uses = 0
    apply_damage(ally.state, ally.state.current_hp)
    ally.state.death_save_failures = 2
    action = HealingAction(
        id="test-heal", name="Test Heal", action_cost="bonus_action", range_ft=60,
        target_mode="self_or_ally", dice_count=1, dice_size=4, healing_bonus=3,
    )
    healer.state.template.healing_actions = [action]

    choice = choose_healing_action(healer, setup)
    assert choice is not None
    chosen_action, target = choice
    assert chosen_action.id == "test-heal"
    assert target.combatant_id == ally.combatant_id

    event = resolve_healing(1, 1, healer, target, action, FixedDiceProvider([4]))
    assert event.hp_before == 0
    assert event.hp_after == 7
    assert ally.state.is_unconscious is False
    assert ally.state.death_save_successes == 0
    assert ally.state.death_save_failures == 0
    assert healer.state.action_available is True
    assert healer.state.bonus_action_available is False


def test_bloodied_ally_is_healed_before_more_injured_self() -> None:
    setup = _setup()
    healer, ally = setup.heroes
    healer.state.current_hp = 1
    ally.state.current_hp = ally.state.template.max_hp // 2
    action = HealingAction(
        id="ally-heal", name="Ally Heal", action_cost="action", range_ft=5,
        target_mode="self_or_ally", healing_bonus=5,
    )
    assert choose_healing_target(healer, setup, action).combatant_id == ally.combatant_id


def test_action_and_bonus_action_self_heals_use_bloodied_threshold() -> None:
    setup = _setup()
    healer = setup.heroes[0]
    action_heal = HealingAction(id="action-heal", name="Action Heal", action_cost="action", target_mode="self", healing_bonus=5)
    bonus_heal = HealingAction(id="bonus-heal", name="Bonus Heal", action_cost="bonus_action", target_mode="self", healing_bonus=5)

    healer.state.current_hp = healer.state.template.max_hp // 2
    assert choose_healing_target(healer, setup, action_heal) is healer
    assert choose_healing_target(healer, setup, bonus_heal) is healer

    healer.state.current_hp = healer.state.template.max_hp
    assert choose_healing_target(healer, setup, action_heal) is None
    assert choose_healing_target(healer, setup, bonus_heal) is None


def test_heal_builder_and_condition_cleansing_are_raw() -> None:
    action = build_heal()
    assert action.healing_bonus == 70
    assert action.resource_id == "spell-slot-6"
    assert action.removable_conditions == ["blinded", "deafened", "poisoned"]

    setup = _setup()
    healer, ally = setup.heroes
    ally.state.current_hp = ally.state.template.max_hp
    ally.state.active_effect_ids.extend(["poisoned", "frightened"])
    cleanse = action.model_copy(update={"resource_id": None})
    assert choose_healing_target(healer, setup, cleanse) is ally
    event = resolve_healing(1, 1, healer, ally, cleanse, FixedDiceProvider([1]))
    assert event.hp_after == ally.state.template.max_hp
    assert event.removed_condition_ids == ["poisoned"]
    assert "poisoned" not in ally.state.active_effect_ids
    assert "frightened" in ally.state.active_effect_ids


def test_reaction_heal_is_not_used_proactively_on_the_healers_turn() -> None:
    setup = _setup()
    healer, ally = setup.heroes
    ally.state.current_hp = 1
    reaction_heal = HealingAction(
        id="reaction-heal", name="Reaction Heal", action_cost="reaction", range_ft=60,
        target_mode="ally", healing_bonus=5,
    )
    healer.state.template.healing_actions = [reaction_heal]
    assert choose_healing_action(healer, setup) is None


def test_action_heal_prevents_charge_attack_and_partial_charge_movement() -> None:
    setup = build_encounter_setup(EncounterSelection(
        hero_ids=["karnok-stoneward-l1"], monster_ids=["srd-giant-goat"],
    ))
    healer, target = setup.monsters[0], setup.heroes[0]
    begin_turn(healer.state)
    healer.state.current_hp = 1
    heal = HealingAction(
        id="self-heal", name="Self Heal", action_cost="action", target_mode="self", healing_bonus=5,
    )
    resolve_healing(1, 1, healer, healer, heal, FixedDiceProvider([1]))
    before = healer.position_ft

    events, _, handled = resolve_charge_closing(2, 1, healer, target, FixedDiceProvider([1]))
    assert handled is False
    assert events == []
    assert healer.position_ft == before
    assert healer.state.action_available is False
