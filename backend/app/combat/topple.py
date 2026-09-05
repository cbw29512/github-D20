from __future__ import annotations

import logging
from dataclasses import dataclass

from app.combat.condition_immunity import condition_is_immune
from app.combat.conditions import PRONE_EFFECT_ID, apply_condition
from app.combat.dice import DiceProvider
from app.combat.saving_throw_rolls import resolve_saving_throw
from app.combat.weapon_mastery import weapon_mastery_active
from app.content.character_math import proficiency_bonus
from app.domain.models import CombatantState, DiceRoll, WeaponAttack

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToppleResolution:
    save_roll: DiceRoll | None = None
    save_dc: int | None = None
    save_succeeded: bool | None = None
    applied: bool = False


def resolve_topple_hit(
    attacker: CombatantState,
    defender: CombatantState,
    attack: WeaponAttack,
    dice: DiceProvider,
) -> ToppleResolution:
    """Resolve the optional 2024 Topple mastery after a successful weapon hit."""
    try:
        if not weapon_mastery_active(attacker, attack, "Topple"):
            return ToppleResolution()
        if defender.is_dead or not defender.is_alive:
            return ToppleResolution()
        if PRONE_EFFECT_ID in defender.active_effect_ids or condition_is_immune(defender, PRONE_EFFECT_ID):
            return ToppleResolution()
        modifier = attack.attack_ability_modifier
        if modifier is None:
            raise ValueError(f"Topple attack {attack.id!r} requires an explicit attack ability modifier.")
        level = attacker.template.level
        if level is None:
            raise ValueError(f"Topple attacker {attacker.template.id!r} requires a certified character level.")
        dc = 8 + modifier + proficiency_bonus(level)
        save_roll, succeeded = resolve_saving_throw(defender, "constitution", dc, dice)
        applied = False if succeeded else apply_condition(defender, PRONE_EFFECT_ID)
        return ToppleResolution(save_roll, dc, succeeded, applied)
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Topple resolution failed for %s.", attacker.template.name)
        raise RuntimeError("Topple mastery could not be resolved.") from exc
