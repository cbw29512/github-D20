from __future__ import annotations

import logging

from app.combat.action_economy import spend
from app.combat.condition_removal_policy import (
    affordable_conditions,
    choose_condition_removal_action,
    costs,
    resource,
    target_allowed,
)
from app.combat.spellcasting import mark_slot_spell_cast, slot_spell_available
from app.domain.encounters import EncounterCombatant
from app.domain.models import BattleEvent, ConditionRemovalAction

logger = logging.getLogger(__name__)


def remove_condition(target: EncounterCombatant, condition_id: str) -> None:
    target.state.active_effect_ids = [item for item in target.state.active_effect_ids if item != condition_id]
    target.state.timed_effects = [item for item in target.state.timed_effects if item.effect_id != condition_id]
    if condition_id == "grappled":
        target.state.grapple_sources = []


def resolve_condition_removal(
    sequence: int,
    round_number: int,
    remover: EncounterCombatant,
    target: EncounterCombatant,
    action: ConditionRemovalAction,
    condition_ids: list[str],
    turn_key: str,
) -> BattleEvent:
    try:
        if action.action_cost == "reaction":
            raise ValueError("Reaction condition removal requires a matching trigger, not an on-turn resolution.")
        if not target_allowed(remover, target, action) or not condition_ids:
            raise ValueError("Condition-removal action is not legal for this target.")
        if action.expends_spell_slot and not slot_spell_available(remover.state, turn_key):
            raise ValueError("A spell slot has already been expended to cast a spell on this turn.")
        legal = set(affordable_conditions(remover, target, action))
        if any(condition_id not in legal for condition_id in condition_ids):
            raise ValueError("Attempted to remove a condition this action cannot legally remove.")
        spend(remover.state, action.action_cost)
        if action.expends_spell_slot:
            mark_slot_spell_cast(remover.state, turn_key)
        for resource_id, cost in costs(action, len(condition_ids)).items():
            item = resource(remover, resource_id)
            if item is None or item.current_uses < cost:
                raise ValueError(f"Required resource {resource_id} is unavailable.")
            item.current_uses -= cost
        for condition_id in condition_ids:
            remove_condition(target, condition_id)
        names = ", ".join(condition_id.replace("_", " ").title() for condition_id in condition_ids)
        return BattleEvent(
            sequence=sequence, round_number=round_number, event_type="feature",
            actor_id=remover.combatant_id, actor_name=remover.state.template.name,
            target_id=target.combatant_id, target_name=target.state.template.name,
            removed_condition_ids=condition_ids, feature_id=action.id,
            animation=action.animation,
            description=f"{remover.state.template.name} uses {action.name} on {target.state.template.name}; {names} ends.",
        )
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Condition removal failed: %s -> %s.", remover.combatant_id, target.combatant_id)
        raise RuntimeError("Condition removal could not be resolved.") from exc


__all__ = ["choose_condition_removal_action", "remove_condition", "resolve_condition_removal"]
