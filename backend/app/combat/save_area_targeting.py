from __future__ import annotations

from app.combat.board_geometry import column_for_slot, slots_in_column
from app.combat.pit_policy import save_distance, target_order
from app.combat.saving_throws import legal_save_action
from app.combat.spell_area import CARD_WIDTH_FT, MAX_CARD_SLOTS
from app.domain.actions import SavingThrowAction
from app.domain.encounters import EncounterCombatant, EncounterSetup


def _living(member: EncounterCombatant) -> bool:
    state = member.state
    return state.is_alive and not state.is_dead and state.current_hp > 0


def _rows(actor: EncounterCombatant, setup: EncounterSetup):
    return (setup.monsters, setup.heroes) if actor.side == "heroes" else (setup.heroes, setup.monsters)


def _forward(actor: EncounterCombatant, member: EncounterCombatant) -> int:
    direction = 1 if actor.side == "heroes" else -1
    return (member.position_ft - actor.position_ft) * direction


def _member_index(member: EncounterCombatant, members: list[EncounterCombatant]) -> int:
    for index, candidate in enumerate(members):
        if candidate.combatant_id == member.combatant_id:
            return index
    raise ValueError(f"{member.combatant_id} is not present in its encounter side.")


def _line_targets(actor: EncounterCombatant, setup: EncounterSetup, action: SavingThrowAction):
    area = action.area
    if area is None or area.shape != "line":
        raise ValueError(f"{action.name} is not a Line area action.")
    if area.width_ft != CARD_WIDTH_FT:
        raise ValueError(f"{action.name} Line widths above 5 feet are not runtime-certified.")
    enemies, friends = _rows(actor, setup)
    column = column_for_slot(_member_index(actor, friends))
    if any(
        column_for_slot(index) == column and member.combatant_id != actor.combatant_id
        and _living(member) and 0 < _forward(actor, member) <= area.size_ft
        for index, member in enumerate(friends)
    ):
        return []
    enemy_slots = set(slots_in_column(column, len(enemies)))
    order = {member.combatant_id: index for index, member in enumerate(target_order(actor, setup))}
    targets = [
        member for index, member in enumerate(enemies)
        if index in enemy_slots and _living(member) and 0 < _forward(actor, member) <= area.size_ft
        and legal_save_action(action, member, save_distance(actor, member, action.range_ft))
    ]
    return sorted(targets, key=lambda member: order.get(member.combatant_id, MAX_CARD_SLOTS))


def _cone_targets(actor: EncounterCombatant, setup: EncounterSetup, action: SavingThrowAction):
    area = action.area
    if area is None or area.shape != "cone" or area.size_ft % CARD_WIDTH_FT:
        raise ValueError(f"{action.name} Cone must use 5-foot card increments.")
    slot_count = min(MAX_CARD_SLOTS, max(1, area.size_ft // CARD_WIDTH_FT))
    enemies, friends = _rows(actor, setup)
    order = {member.combatant_id: index for index, member in enumerate(target_order(actor, setup))}
    candidates = []
    for start in range(MAX_CARD_SLOTS - slot_count + 1):
        targets = [
            member for index, member in enumerate(enemies)
            if start <= index < start + slot_count and _living(member)
            and 0 < _forward(actor, member) <= area.size_ft
            and legal_save_action(action, member, save_distance(actor, member, action.range_ft))
        ]
        exposed = any(
            member.combatant_id != actor.combatant_id and start <= index < start + slot_count
            and _living(member) and 0 < _forward(actor, member) <= area.size_ft
            for index, member in enumerate(friends)
        )
        if targets and not exposed:
            targets.sort(key=lambda member: order.get(member.combatant_id, MAX_CARD_SLOTS))
            candidates.append((len(targets), -start, targets))
    return max(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else []


def area_targets(actor: EncounterCombatant, setup: EncounterSetup, action: SavingThrowAction):
    if action.area is None:
        return []
    if action.area.shape == "line":
        return _line_targets(actor, setup, action)
    if action.area.shape == "cone":
        return _cone_targets(actor, setup, action)
    raise ValueError(f"{action.name} area shape {action.area.shape!r} is not runtime-certified.")


def targets_for_action(actor: EncounterCombatant, setup: EncounterSetup, action: SavingThrowAction):
    if action.area is not None:
        return area_targets(actor, setup, action)
    return next((
        [target] for target in target_order(actor, setup)
        if legal_save_action(action, target, save_distance(actor, target, action.range_ft))
    ), [])
