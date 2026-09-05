from __future__ import annotations

import logging

from app.combat.attack_resources import spend_attack_resource
from app.combat.cleave import resolve_cleave_extra_attack
from app.combat.encounter_attacks import resolve_encounter_attack
from app.combat.light_attack_resolution import resolve_light_extra_attack
from app.domain.encounters import EncounterCombatant, EncounterSetup
from app.domain.models import BattleEvent, WeaponAttack

logger = logging.getLogger(__name__)


def resolve_standard_attack_action(
    sequence: int,
    round_number: int,
    attacker: EncounterCombatant,
    target: EncounterCombatant,
    attack: WeaponAttack,
    distance_ft: int,
    dice,
    setup: EncounterSetup,
    turn_key: str,
    *,
    advantage_sources: int = 0,
    feature_id: str | None = None,
    allow_reckless: bool = True,
) -> tuple[list[BattleEvent], int]:
    """Resolve one Attack action plus optional mastery/Light follow-up."""
    try:
        spend_attack_resource(attacker.state, attack)
        event = resolve_encounter_attack(
            sequence,
            round_number,
            attacker,
            target,
            attack,
            distance_ft,
            dice,
            setup,
            advantage_sources=advantage_sources,
            feature_id=feature_id,
            turn_key=turn_key,
            allow_reckless=allow_reckless,
        )
        events = [event]
        sequence += 1
        cleave, sequence = resolve_cleave_extra_attack(
            sequence, round_number, attacker, event, attack, setup, dice, turn_key,
        )
        events.extend(cleave)
        if attacker.state.template.kind != "character" or not attack.weapon.light:
            return events, sequence
        more, sequence = resolve_light_extra_attack(
            sequence,
            round_number,
            attacker,
            setup,
            dice,
            attack,
            turn_key,
        )
        events.extend(more)
        return events, sequence
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Standard Attack action failed for %s.", attacker.combatant_id)
        raise RuntimeError("Standard Attack action could not be resolved.") from exc
