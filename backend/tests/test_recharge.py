from __future__ import annotations

import pytest

from app.combat.dice import FixedDiceProvider
from app.combat.recharge import resolve_recharge_start_of_turn
from app.combat.resource_pool import get_resource
from app.combat.state import build_combatant_state
from app.content.audited_fighter import build_karnok_stoneward
from app.domain.combatants import RechargeDefinition
from app.domain.models import ResourceState


def _state():
    state = build_combatant_state(build_karnok_stoneward())
    state.resources.append(ResourceState(id="fire-breath", name="Fire Breath", current_uses=0, max_uses=1))
    return state


def test_recharge_success_restores_shared_resource() -> None:
    state = _state()
    rule = RechargeDefinition(minimum=5, maximum=6)
    result = resolve_recharge_start_of_turn(state, "fire-breath", rule, FixedDiceProvider([5]))
    assert result.roll == 5
    assert result.recharged is True
    assert result.resource_remaining == 1
    assert get_resource(state, "fire-breath").current_uses == 1


def test_recharge_failure_leaves_ability_spent() -> None:
    state = _state()
    rule = RechargeDefinition(minimum=5, maximum=6)
    result = resolve_recharge_start_of_turn(state, "fire-breath", rule, FixedDiceProvider([4]))
    assert result.roll == 4
    assert result.recharged is False
    assert result.resource_remaining == 0


def test_recharge_does_not_roll_when_resource_is_already_ready() -> None:
    state = _state()
    get_resource(state, "fire-breath").current_uses = 1
    dice = FixedDiceProvider([6])
    result = resolve_recharge_start_of_turn(
        state, "fire-breath", RechargeDefinition(minimum=5), dice,
    )
    assert result.roll is None
    assert result.recharged is False
    assert dice.roll(6) == 6


def test_recharge_definition_rejects_invalid_range() -> None:
    with pytest.raises(ValueError, match="range"):
        RechargeDefinition(minimum=6, maximum=5)
