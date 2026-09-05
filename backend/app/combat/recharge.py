from __future__ import annotations

import logging
from dataclasses import dataclass

from app.combat.dice import DiceProvider
from app.combat.resource_pool import get_resource, restore_resource
from app.domain.combatants import RechargeDefinition
from app.domain.models import CombatantState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RechargeResult:
    roll: int | None
    recharged: bool
    resource_remaining: int


def resolve_recharge_start_of_turn(
    state: CombatantState,
    resource_id: str,
    rule: RechargeDefinition,
    dice: DiceProvider,
) -> RechargeResult:
    """Resolve one declarative Recharge rule for a spent runtime resource."""
    try:
        item = get_resource(state, resource_id)
        if item is None:
            raise ValueError(f"Recharge resource {resource_id!r} is missing.")
        if item.current_uses >= item.max_uses:
            return RechargeResult(None, False, item.current_uses)
        roll = dice.roll(rule.die_size)
        recharged = rule.minimum <= roll <= rule.maximum
        if recharged:
            item = restore_resource(state, resource_id)
        return RechargeResult(roll, recharged, item.current_uses)
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Recharge failed for %s resource %s.", state.template.name, resource_id)
        raise RuntimeError("Recharge could not be resolved.") from exc
