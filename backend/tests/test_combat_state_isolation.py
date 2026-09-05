from app.combat.state import build_combatant_state
from app.content.demo import build_demo_fighter


def test_runtime_state_deep_copies_source_card_definition() -> None:
    source = build_demo_fighter()

    state = build_combatant_state(source)

    assert state.template is not source
    assert state.template.weapon_attack is not source.weapon_attack
    assert state.template.resources is not source.resources


def test_runtime_template_mutation_cannot_change_source_card() -> None:
    source = build_demo_fighter()
    original_ac = source.armor_class
    original_immunities = list(source.condition_immunities)

    state = build_combatant_state(source)
    state.template.armor_class += 5
    state.template.condition_immunities.append("poisoned")

    assert source.armor_class == original_ac
    assert source.condition_immunities == original_immunities


def test_new_fight_starts_from_immutable_source_not_previous_runtime() -> None:
    source = build_demo_fighter()
    first = build_combatant_state(source)
    first.current_hp = 1
    first.template.armor_class += 5
    first.resources[0].current_uses = 0

    second = build_combatant_state(source)

    assert second.current_hp == source.max_hp
    assert second.template.armor_class == source.armor_class
    assert second.resources[0].current_uses == second.resources[0].max_uses
