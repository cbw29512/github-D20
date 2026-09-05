from __future__ import annotations

import logging
from typing import Literal

from app.combat.concentration import resolve_concentration_damage
from app.combat.conditions import PRONE_EFFECT_ID, apply_condition
from app.combat.dice import DiceProvider
from app.combat.hit_points import effective_max_hp
from app.combat.orc import use_relentless_endurance
from app.combat.source_bound_effects import end_damage_sensitive_effects
from app.combat.undead_fortitude import resolve_undead_fortitude
from app.domain.models import CombatantState, DamageType
from app.domain.traits import CombatTrait

logger = logging.getLogger(__name__)
ZeroHpOutcome = Literal[
    "damaged", "unconscious", "dead", "unchanged", "relentless_endurance", "undead_fortitude",
]
DODGE_EFFECT_ID = "dodge"


def reset_death_saves(state: CombatantState) -> None:
    state.death_save_successes = 0
    state.death_save_failures = 0


def _mark_dead(state: CombatantState) -> ZeroHpOutcome:
    state.current_hp = 0
    state.is_alive = False
    state.is_dead = True
    state.is_unconscious = False
    state.is_stable = False
    state.active_effect_ids = [effect for effect in state.active_effect_ids if effect != DODGE_EFFECT_ID]
    return "dead"


def _mark_unconscious(state: CombatantState) -> ZeroHpOutcome:
    state.is_alive = True
    state.is_unconscious = True
    state.is_stable = False
    state.active_effect_ids = [effect for effect in state.active_effect_ids if effect != DODGE_EFFECT_ID]
    apply_condition(state, PRONE_EFFECT_ID)
    return "unconscious"


def _after_temporary_hp(state: CombatantState, amount: int) -> int:
    absorbed = min(state.temporary_hp, amount)
    state.temporary_hp -= absorbed
    return amount - absorbed


def _finish_damage(
    state: CombatantState,
    outcome: ZeroHpOutcome,
    damage_taken: int,
    dice: DiceProvider | None,
    affected_states: list[CombatantState] | None,
) -> ZeroHpOutcome:
    end_damage_sensitive_effects(state)
    if state.concentration is None:
        return outcome
    if dice is None:
        if state.is_dead or state.is_unconscious:
            from app.combat.concentration import end_concentration_if_incapacitated
            end_concentration_if_incapacitated(state, affected_states)
            return outcome
        raise ValueError("A dice provider is required to resolve Concentration damage.")
    resolve_concentration_damage(state, damage_taken, dice, affected_states)
    return outcome


def restore_hit_points(state: CombatantState, amount: int) -> int:
    """Restore true HP; ordinary healing cannot restore a dead creature or a Swarm."""
    if amount < 0:
        raise ValueError("Healing cannot be negative.")
    if state.is_dead or amount == 0 or CombatTrait.SWARM in state.template.combat_traits:
        return 0
    before = state.current_hp
    state.current_hp = min(effective_max_hp(state), before + amount)
    healed = state.current_hp - before
    if healed > 0:
        state.is_alive = True
        state.is_unconscious = False
        state.is_stable = False
        reset_death_saves(state)
    return healed


def _damage_at_zero(state: CombatantState, incoming: int, *, critical: bool) -> ZeroHpOutcome:
    if state.template.kind == "monster" or incoming >= effective_max_hp(state):
        return _mark_dead(state)
    state.is_stable = False
    state.death_save_failures = min(3, state.death_save_failures + (2 if critical else 1))
    if state.death_save_failures >= 3:
        return _mark_dead(state)
    return _mark_unconscious(state)


def apply_damage(
    state: CombatantState,
    amount: int,
    *,
    critical: bool = False,
    damage_types: set[DamageType] | None = None,
    dice: DiceProvider | None = None,
    affected_states: list[CombatantState] | None = None,
) -> ZeroHpOutcome:
    """Apply Temporary HP, Concentration, and SRD 5.2.1 zero-HP lifecycle rules."""
    try:
        if amount < 0:
            raise ValueError("Damage cannot be negative.")
        if amount == 0 or state.is_dead:
            return "unchanged"

        incoming = amount
        types = damage_types or set()
        amount = _after_temporary_hp(state, amount)
        if state.current_hp == 0:
            return _finish_damage(state, _damage_at_zero(state, incoming, critical=critical), incoming, dice, affected_states)
        if amount == 0:
            return _finish_damage(state, "damaged", incoming, dice, affected_states)

        hp_before = state.current_hp
        state.current_hp = max(0, hp_before - amount)
        if state.current_hp > 0:
            return _finish_damage(state, "damaged", incoming, dice, affected_states)
        if resolve_undead_fortitude(
            state, incoming, types, critical=critical, dice=dice,
        ):
            return _finish_damage(state, "undead_fortitude", incoming, dice, affected_states)
        if state.template.kind == "monster":
            return _finish_damage(state, _mark_dead(state), incoming, dice, affected_states)

        remaining_damage = max(0, amount - hp_before)
        if remaining_damage >= effective_max_hp(state):
            return _finish_damage(state, _mark_dead(state), incoming, dice, affected_states)
        if use_relentless_endurance(state, remaining_damage):
            return _finish_damage(state, "relentless_endurance", incoming, dice, affected_states)
        return _finish_damage(state, _mark_unconscious(state), incoming, dice, affected_states)
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Zero-HP damage resolution failed for %s.", state.template.name)
        raise RuntimeError("Zero-HP damage could not be resolved.") from exc
