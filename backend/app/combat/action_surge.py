from __future__ import annotations

from app.combat.condition_rules import is_incapacitated
from app.combat.resource_pool import get_resource, resource_uses, spend_resource
from app.domain.models import BattleEvent, CombatantState

ACTION_SURGE = "action-surge"


def action_surge_available(state: CombatantState, turn_key: str) -> bool:
    return bool(
        resource_uses(state, ACTION_SURGE) > 0
        and not state.action_available
        and not state.is_dead
        and not is_incapacitated(state)
        and state.feature_last_turn_keys.get(ACTION_SURGE) != turn_key
    )


def use_action_surge(
    sequence: int,
    round_number: int,
    actor_id: str,
    state: CombatantState,
    turn_key: str,
) -> BattleEvent:
    """Grant Fighter's additional non-Magic Action once on this turn."""
    if not action_surge_available(state, turn_key):
        raise ValueError("Action Surge is not available.")
    resource = spend_resource(state, ACTION_SURGE)
    state.action_available = True
    state.feature_last_turn_keys[ACTION_SURGE] = turn_key
    return BattleEvent(
        sequence=sequence,
        round_number=round_number,
        event_type="feature",
        actor_id=actor_id,
        actor_name=state.template.name,
        feature_id=ACTION_SURGE,
        resource_remaining=resource.current_uses,
        animation=ACTION_SURGE,
        description=f"{state.template.name} uses Action Surge and gains one additional Action.",
    )
