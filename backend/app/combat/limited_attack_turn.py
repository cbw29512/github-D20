from __future__ import annotations

from app.combat.pit_policy import choose_resource_backed_attack
from app.combat.standard_attack_action import resolve_standard_attack_action
from app.domain.encounters import EncounterCombatant, EncounterSetup
from app.domain.models import BattleEvent


def resolve_resource_backed_attack_turn(
    sequence: int,
    round_number: int,
    attacker: EncounterCombatant,
    setup: EncounterSetup,
    dice,
    turn_key: str,
) -> tuple[list[BattleEvent], int, bool]:
    """Prefer one available limited-use attack before repeatable offense."""
    choice = choose_resource_backed_attack(attacker, setup)
    if choice is None:
        return [], sequence, False
    target, attack, distance = choice
    events, sequence = resolve_standard_attack_action(
        sequence,
        round_number,
        attacker,
        target,
        attack,
        distance,
        dice,
        setup,
        turn_key,
        feature_id=attack.resource_id,
    )
    return events, sequence, True
