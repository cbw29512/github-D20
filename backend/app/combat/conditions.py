from __future__ import annotations

from app.combat.condition_immunity import condition_is_immune
from app.combat.condition_rules import attacks_have_advantage_against, has_condition
from app.combat.grapple import (
    RESTRAINED_EFFECT_ID,
    apply_grapple,
    grapple_attack_disadvantage,
    speed_is_zero,
)
from app.combat.hit_modifiers import apply_hit_modifier_effects
from app.combat.modifier_stack import effective_speed
from app.combat.timed_conditions import apply_timed_condition
from app.domain.models import CombatantState, WeaponAttack
from app.domain.size import size_at_most

BLINDED_EFFECT_ID = "blinded"
DODGE_EFFECT_ID = "dodge"
FRIGHTENED_EFFECT_ID = "frightened"
POISONED_EFFECT_ID = "poisoned"
PRONE_EFFECT_ID = "prone"


def apply_condition(state: CombatantState, condition_id: str) -> bool:
    """Apply one shared condition state when the target is eligible."""
    if state.is_dead or not state.is_alive:
        return False
    if condition_is_immune(state, condition_id):
        return False
    if condition_id in state.active_effect_ids:
        return False
    state.active_effect_ids.append(condition_id)
    return True


def attack_roll_condition_sources(
    attacker: CombatantState,
    defender: CombatantState,
    distance_ft: int,
    target_id: str | None = None,
) -> tuple[int, int]:
    """Return Advantage and Disadvantage sources from supported conditions."""
    advantage = 0
    disadvantage = 0
    if has_condition(attacker, BLINDED_EFFECT_ID):
        disadvantage += 1
    if has_condition(attacker, FRIGHTENED_EFFECT_ID):
        disadvantage += 1
    if PRONE_EFFECT_ID in attacker.active_effect_ids:
        disadvantage += 1
    if RESTRAINED_EFFECT_ID in attacker.active_effect_ids:
        disadvantage += 1
    if POISONED_EFFECT_ID in attacker.active_effect_ids:
        disadvantage += 1
    if target_id is not None:
        disadvantage += grapple_attack_disadvantage(attacker, target_id)
    if (
        DODGE_EFFECT_ID in defender.active_effect_ids
        and not attacks_have_advantage_against(defender)
        and not speed_is_zero(defender)
        and effective_speed(defender) > 0
    ):
        disadvantage += 1
    if attacks_have_advantage_against(defender):
        advantage += 1
    if RESTRAINED_EFFECT_ID in defender.active_effect_ids:
        advantage += 1
    if PRONE_EFFECT_ID in defender.active_effect_ids:
        if distance_ft <= 5:
            advantage += 1
        else:
            disadvantage += 1
    return advantage, disadvantage


def apply_hit_conditions(
    attack: WeaponAttack,
    defender: CombatantState,
    source_id: str,
    round_number: int | None = None,
    affected_states: list[CombatantState] | None = None,
) -> list[str]:
    """Apply certified automatic conditions and modifiers from a successful weapon hit."""
    if defender.is_dead or not defender.is_alive:
        return []
    apply_hit_modifier_effects(defender, source_id, attack)
    applied: list[str] = []
    maximum = attack.knocks_prone_max_size
    if maximum is not None and size_at_most(defender.template.size, maximum):
        if apply_condition(defender, PRONE_EFFECT_ID):
            applied.append(PRONE_EFFECT_ID)
    control = attack.control_effect
    if control is not None and control.grapple_escape_dc is not None:
        if control.max_target_size is None or size_at_most(defender.template.size, control.max_target_size):
            applied.extend(apply_grapple(
                defender,
                source_id,
                control.grapple_escape_dc,
                attack.weapon.reach_ft,
                restrains=control.restrains_while_grappled,
            ))
    if control is not None and control.condition_id is not None:
        timed = apply_timed_condition(
            defender,
            control.condition_id,
            source_id,
            source_effect_id=attack.id,
            applied_round=round_number,
            expires_at_start_of_source_turn=control.expires_at_start_of_source_turn,
            expiry_timing=control.expiry_timing,
            repeat_save_ability=control.repeat_save_ability,
            repeat_save_dc=control.repeat_save_dc,
            repeat_save_timing=control.repeat_save_timing,
            allowed_removal_action_ids=control.allowed_removal_action_ids,
            affected_states=affected_states,
        )
        if timed is not None:
            applied.append(timed)
    return list(dict.fromkeys(applied))


def stand_from_prone(state: CombatantState) -> int:
    """Spend half effective Speed at turn start to end Prone when standing is possible."""
    speed = effective_speed(state)
    if PRONE_EFFECT_ID not in state.active_effect_ids or speed <= 0 or speed_is_zero(state):
        return 0
    movement_cost = speed // 2
    state.movement_remaining_ft = max(0, state.movement_remaining_ft - movement_cost)
    state.active_effect_ids.remove(PRONE_EFFECT_ID)
    return movement_cost
