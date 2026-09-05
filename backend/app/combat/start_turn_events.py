from __future__ import annotations

import logging

from app.combat.dice import DiceProvider
from app.combat.recharge import resolve_recharge_start_of_turn
from app.domain.encounters import EncounterCombatant
from app.domain.models import BattleEvent

logger = logging.getLogger(__name__)


def resolve_start_turn_recharges(
    sequence: int,
    round_number: int,
    member: EncounterCombatant,
    dice: DiceProvider,
) -> tuple[list[BattleEvent], int]:
    """Resolve every spent declarative Recharge resource at START_OF_TURN."""
    try:
        events: list[BattleEvent] = []
        for definition in member.state.template.resources:
            if definition.recharge is None:
                continue
            result = resolve_recharge_start_of_turn(
                member.state, definition.id, definition.recharge, dice,
            )
            if result.roll is None:
                continue
            outcome = "recharges" if result.recharged else "does not recharge"
            events.append(BattleEvent(
                sequence=sequence,
                round_number=round_number,
                event_type="feature",
                actor_id=member.combatant_id,
                actor_name=member.state.template.name,
                feature_id=definition.id,
                resource_remaining=result.resource_remaining,
                animation="recharge",
                description=(
                    f"{member.state.template.name} rolls {result.roll} for "
                    f"{definition.name} Recharge and {outcome}."
                ),
            ))
            sequence += 1
        return events, sequence
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Start-turn Recharge failed for %s.", member.combatant_id)
        raise RuntimeError("Start-turn Recharge could not be resolved.") from exc
