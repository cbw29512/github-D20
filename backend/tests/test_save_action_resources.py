from __future__ import annotations

import pytest

from app.combat.dice import FixedDiceProvider
from app.combat.saving_throws import resolve_save_action, save_action_resource_available
from app.combat.state import build_combatant_state
from app.content.audited_fighter import build_karnok_stoneward
from app.domain.combatants import ResourceDefinition
from app.domain.encounters import EncounterCombatant
from app.domain.models import SavingThrowAction


def _members():
    actor_template = build_karnok_stoneward().model_copy(deep=True)
    actor_template.resources.append(ResourceDefinition(id="test-breath", name="Test Breath", max_uses=1))
    actor = EncounterCombatant(
        combatant_id="hero-1:tester", side="heroes", position_ft=5,
        state=build_combatant_state(actor_template),
    )
    target = EncounterCombatant(
        combatant_id="monster-1:target", side="monsters", position_ft=10,
        state=build_combatant_state(build_karnok_stoneward()),
    )
    return actor, target


def _action() -> SavingThrowAction:
    return SavingThrowAction(
        id="test-breath", name="Test Breath", save_ability="dexterity", dc=20, range_ft=15,
        damage_dice_count=1, damage_dice_size=6, damage_type="fire", success_damage="half",
        resource_id="test-breath", resource_cost=1,
    )


def test_save_action_spends_shared_resource_once() -> None:
    actor, target = _members(); action = _action()
    event = resolve_save_action(1, 1, actor, target, action, 5, FixedDiceProvider([10, 4]))
    assert actor.state.resources[-1].current_uses == 0
    assert event.resource_remaining == 0
    assert not save_action_resource_available(actor.state, action)


def test_spent_save_action_resource_fails_closed_before_rolling() -> None:
    actor, target = _members(); action = _action()
    actor.state.resources[-1].current_uses = 0
    with pytest.raises(ValueError, match="resource is unavailable"):
        resolve_save_action(1, 1, actor, target, action, 5, FixedDiceProvider([20]))
