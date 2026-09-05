from __future__ import annotations

from app.combat.action_economy import is_available
from app.combat.pit_policy import save_distance
from app.combat.save_area_targeting import targets_for_action
from app.combat.saving_throws import resolve_save_action, save_action_resource_available
from app.domain.encounters import EncounterCombatant, EncounterSetup
from app.domain.models import BattleEvent


def resolve_save_action_turn(
    sequence: int, round_number: int, actor: EncounterCombatant, setup: EncounterSetup, dice,
    *, resource_backed_only: bool,
) -> tuple[list[BattleEvent], int, bool]:
    if not is_available(actor.state, "action"):
        return [], sequence, False
    affected = [member.state for member in [*setup.heroes, *setup.monsters]]
    for action in actor.state.template.saving_throw_actions:
        if resource_backed_only != (action.resource_id is not None):
            continue
        if not save_action_resource_available(actor.state, action):
            continue
        targets = targets_for_action(actor, setup, action)
        if not targets:
            continue
        events: list[BattleEvent] = []
        shared_damage_rolls: list[int] | None = None
        for index, target in enumerate(targets):
            event = resolve_save_action(
                sequence, round_number, actor, target, action,
                save_distance(actor, target, action.range_ft), dice,
                spend_action=index == 0, spend_resource_cost=index == 0,
                shared_damage_rolls=shared_damage_rolls, affected_states=affected,
            )
            events.append(event)
            sequence += 1
            if shared_damage_rolls is None and event.damage_components:
                shared_damage_rolls = list(event.damage_components[0].rolls)
        return events, sequence, True
    return [], sequence, False
