from __future__ import annotations

from app.combat.dice import FixedDiceProvider
from app.combat.resource_pool import get_resource
from app.combat.start_turn_events import resolve_start_turn_recharges
from app.combat.state import build_combatant_state
from app.content.audited_fighter import build_karnok_stoneward
from app.domain.combatants import RechargeDefinition, ResourceDefinition
from app.domain.encounters import EncounterCombatant


def _member() -> EncounterCombatant:
    template = build_karnok_stoneward().model_copy(deep=True)
    template.resources.append(ResourceDefinition(
        id="fire-breath",
        name="Fire Breath",
        max_uses=1,
        recharge=RechargeDefinition(minimum=5, maximum=6),
    ))
    state = build_combatant_state(template)
    get_resource(state, "fire-breath").current_uses = 0
    return EncounterCombatant(combatant_id="dragon-1", side="monsters", position_ft=30, state=state)


def test_start_turn_recharge_uses_declarative_resource_and_logs_source_name() -> None:
    member = _member()
    events, sequence = resolve_start_turn_recharges(7, 2, member, FixedDiceProvider([6]))
    assert sequence == 8
    assert len(events) == 1
    assert events[0].feature_id == "fire-breath"
    assert events[0].resource_remaining == 1
    assert "Fire Breath" in events[0].description
    assert "rolls 6" in events[0].description


def test_start_turn_recharge_skips_ready_resource_without_consuming_die() -> None:
    member = _member()
    get_resource(member.state, "fire-breath").current_uses = 1
    dice = FixedDiceProvider([4])
    events, sequence = resolve_start_turn_recharges(3, 1, member, dice)
    assert events == []
    assert sequence == 3
    assert dice.roll(6) == 4
