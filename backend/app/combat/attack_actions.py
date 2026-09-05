from __future__ import annotations

import logging

from app.combat.action_economy import is_available, spend
from app.combat.ally_context import pack_tactics_active
from app.combat.attack_action_rules import validate_attack_action_slots
from app.combat.attack_resources import spend_attack_resource
from app.combat.cleave import resolve_cleave_extra_attack
from app.combat.dice import DiceProvider
from app.combat.encounter_attacks import resolve_encounter_attack
from app.combat.light_attack_resolution import resolve_light_extra_attack
from app.combat.opening_burst import opening_feature_id
from app.combat.pit_policy import (
    allied_frontline_active,
    choose_attack,
    flexible_slot_has_both,
    has_backline_target,
    has_frontline_target,
    is_backline,
    save_distance,
    target_order,
)
from app.combat.saving_throws import legal_save_action, resolve_save_action, save_action_resource_available
from app.domain.encounters import EncounterCombatant, EncounterSetup
from app.domain.models import BattleEvent, WeaponAttack, WeaponAttackKind

logger = logging.getLogger(__name__)


def _save_choice(attacker, setup, slot):
    allowed = set(slot.save_action_ids)
    for target in target_order(attacker, setup):
        for action in attacker.state.template.saving_throw_actions:
            if action.id not in allowed or not save_action_resource_available(attacker.state, action):
                continue
            distance = save_distance(attacker, target, action.range_ft)
            if legal_save_action(action, target, distance):
                return target, action, distance
    return None


def _attack_choice(attacker, setup, slot, *, ranged_backline: bool = False):
    if ranged_backline:
        choice = choose_attack(attacker, setup, slot.attack_ids, kind=WeaponAttackKind.RANGED, prefer_backline=True)
        if choice is not None:
            return choice
    if is_backline(attacker) and allied_frontline_active(attacker, setup):
        ranged = choose_attack(attacker, setup, slot.attack_ids, kind=WeaponAttackKind.RANGED)
        if ranged is not None:
            return ranged
    melee = choose_attack(attacker, setup, slot.attack_ids, kind=WeaponAttackKind.MELEE)
    if melee is not None:
        return melee
    return choose_attack(attacker, setup, slot.attack_ids, kind=WeaponAttackKind.RANGED)


def _use_ranged_split(attacker, setup, slots, dice: DiceProvider) -> bool:
    if is_backline(attacker):
        return False
    if not has_frontline_target(attacker, setup) or not has_backline_target(attacker, setup):
        return False
    if not any(flexible_slot_has_both(attacker, slot.attack_ids) for slot in slots[1:]):
        return False
    return dice.roll(100) >= 76


def resolve_attack_action(
    sequence: int, round_number: int, attacker: EncounterCombatant,
    setup: EncounterSetup, dice: DiceProvider,
) -> tuple[list[BattleEvent], int]:
    """Resolve Multiattack/Extra Attack in fixed Pit formation with role-aware targeting."""
    try:
        validate_attack_action_slots(attacker)
        definition = attacker.state.template.attack_action
        if definition is None or not is_available(attacker.state, "action"):
            raise ValueError("Attack action or Multiattack is not available.")
        if not target_order(attacker, setup):
            return [], sequence

        spend(attacker.state, "action")
        events: list[BattleEvent] = []
        opening_feature = opening_feature_id(round_number, attacker, setup)
        affected_states = [member.state for member in [*setup.heroes, *setup.monsters]]
        light_trigger: WeaponAttack | None = None
        ranged_split = _use_ranged_split(attacker, setup, definition.slots, dice)
        ranged_split_used = False
        turn_key = f"{round_number}:{attacker.combatant_id}"

        for index, slot in enumerate(definition.slots):
            if attacker.state.is_dead or attacker.state.is_unconscious:
                break
            split_this_slot = index > 0 and ranged_split and not ranged_split_used and flexible_slot_has_both(attacker, slot.attack_ids)
            attack_choice = _attack_choice(attacker, setup, slot, ranged_backline=split_this_slot)
            if attack_choice is not None:
                target, attack, distance = attack_choice
                spend_attack_resource(attacker.state, attack)
                if split_this_slot and attack.weapon.attack_kind is WeaponAttackKind.RANGED:
                    ranged_split_used = True
                pack = pack_tactics_active(attacker, target, setup)
                feature_id = opening_feature or ("pack-tactics" if pack else definition.id)
                event = resolve_encounter_attack(
                    sequence, round_number, attacker, target, attack, distance, dice, setup,
                    spend_action=False, advantage_sources=1 if pack else 0,
                    feature_id=feature_id, turn_key=turn_key, allow_reckless=True,
                    close_enemy_active=False,
                )
                events.append(event)
                sequence += 1
                cleave, sequence = resolve_cleave_extra_attack(sequence, round_number, attacker, event, attack, setup, dice, turn_key)
                events.extend(cleave)
                if definition.is_attack_action and light_trigger is None and attack.weapon.light:
                    light_trigger = attack
                opening_feature = None
                continue

            save_choice = _save_choice(attacker, setup, slot)
            if save_choice is not None:
                target, save_action, distance = save_choice
                events.append(resolve_save_action(
                    sequence, round_number, attacker, target, save_action,
                    distance, dice, spend_action=False, affected_states=affected_states,
                ))
                sequence += 1

        if definition.is_attack_action and light_trigger is not None:
            more, sequence = resolve_light_extra_attack(sequence, round_number, attacker, setup, dice, light_trigger, turn_key)
            events.extend(more)
        return events, sequence
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Attack action sequence failed for %s.", attacker.combatant_id)
        raise RuntimeError("Attack action sequence could not be resolved.") from exc
