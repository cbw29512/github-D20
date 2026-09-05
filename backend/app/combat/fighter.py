from __future__ import annotations

import logging

from app.combat.action_economy import is_available, spend
from app.combat.dice import DiceProvider
from app.combat.resource_pool import resource_uses, spend_resource
from app.combat.zero_hp import restore_hit_points
from app.domain.models import BattleEvent, CombatantState, DiceRoll

logger = logging.getLogger(__name__)
SECOND_WIND = "second-wind"


def use_second_wind(
    sequence: int,
    round_number: int,
    fighter: CombatantState,
    dice: DiceProvider,
    actor_event_id: str | None = None,
) -> BattleEvent:
    """Apply the SRD 5.2.1 Second Wind healing/resource rules to a Fighter state."""
    try:
        if resource_uses(fighter, SECOND_WIND) <= 0:
            raise ValueError("Second Wind has no remaining uses.")
        if not is_available(fighter, "bonus_action"):
            raise ValueError("Bonus Action is not available.")
        if fighter.template.level is None:
            raise ValueError("Second Wind requires a Fighter level.")

        rolled = dice.roll(10)
        healing_roll = DiceRoll(
            notation=f"1d10+{fighter.template.level}",
            rolls=[rolled],
            modifier=fighter.template.level,
            total=rolled + fighter.template.level,
        )
        hp_before = fighter.current_hp
        healed = restore_hit_points(fighter, healing_roll.total)
        spend(fighter, "bonus_action")
        resource = spend_resource(fighter, SECOND_WIND)
        event_id = actor_event_id or fighter.template.id

        return BattleEvent(
            sequence=sequence,
            round_number=round_number,
            event_type="healing",
            actor_id=event_id,
            actor_name=fighter.template.name,
            target_id=event_id,
            target_name=fighter.template.name,
            healing_roll=healing_roll,
            hp_before=hp_before,
            hp_after=fighter.current_hp,
            feature_id=SECOND_WIND,
            resource_remaining=resource.current_uses,
            animation=SECOND_WIND,
            description=f"{fighter.template.name} uses Second Wind and regains {healed} HP.",
        )
    except Exception as exc:
        logger.exception("Second Wind resolution failed for %s.", fighter.template.name)
        raise RuntimeError("Second Wind could not be resolved.") from exc
