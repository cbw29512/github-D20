from __future__ import annotations

import logging

from app.combat.attack_legality import attack_allowed_against
from app.combat.attack_resources import attack_resource_available
from app.combat.encounter_targeting import combatant_distance, living_opponents
from app.combat.formation import uses_backline
from app.domain.encounters import EncounterCombatant, EncounterSetup
from app.domain.models import WeaponAttack, WeaponAttackKind

logger = logging.getLogger(__name__)


def is_backline(member: EncounterCombatant) -> bool:
    return uses_backline(member.state.template)


def target_order(
    attacker: EncounterCombatant,
    setup: EncounterSetup,
    *,
    prefer_backline: bool = False,
) -> list[EncounterCombatant]:
    """Return active Pit targets by formation role without using movement distance as priority."""
    opponents = living_opponents(attacker, setup)
    front = [target for target in opponents if not is_backline(target)]
    back = [target for target in opponents if is_backline(target)]
    return [*back, *front] if prefer_backline else [*front, *back]


def has_frontline_target(attacker: EncounterCombatant, setup: EncounterSetup) -> bool:
    return any(not is_backline(target) for target in living_opponents(attacker, setup))


def has_backline_target(attacker: EncounterCombatant, setup: EncounterSetup) -> bool:
    return any(is_backline(target) for target in living_opponents(attacker, setup))


def allied_frontline_active(attacker: EncounterCombatant, setup: EncounterSetup) -> bool:
    allies = setup.heroes if attacker.side == "heroes" else setup.monsters
    return any(
        ally.combatant_id != attacker.combatant_id
        and ally.state.is_alive
        and not ally.state.is_dead
        and ally.state.current_hp > 0
        and not is_backline(ally)
        for ally in allies
    )


def attack_distance(attacker: EncounterCombatant, target: EncounterCombatant, attack: WeaponAttack) -> int:
    """Collapse ordinary movement: a legal Pit attack is resolved at reach or normal range without moving cards."""
    actual = combatant_distance(attacker, target)
    weapon = attack.weapon
    if weapon.attack_kind is WeaponAttackKind.MELEE:
        return min(actual, weapon.reach_ft)
    if weapon.normal_range_ft is None:
        raise ValueError(f"Ranged attack {attack.id!r} has no normal range.")
    return min(actual, weapon.normal_range_ft)


def save_distance(attacker: EncounterCombatant, target: EncounterCombatant, range_ft: int) -> int:
    if range_ft < 0:
        raise ValueError("Save-action range cannot be negative.")
    return min(combatant_distance(attacker, target), range_ft)


def _attack_profiles(attacker: EncounterCombatant, allowed_ids: list[str], kind: WeaponAttackKind | None):
    allowed = set(allowed_ids)
    return [
        attack
        for attack in [attacker.state.template.weapon_attack, *attacker.state.template.alternate_weapon_attacks]
        if attack.id in allowed
        and (kind is None or attack.weapon.attack_kind is kind)
        and attack_resource_available(attacker.state, attack)
    ]


def choose_attack(
    attacker: EncounterCombatant,
    setup: EncounterSetup,
    allowed_ids: list[str],
    *,
    kind: WeaponAttackKind | None = None,
    prefer_backline: bool = False,
) -> tuple[EncounterCombatant, WeaponAttack, int] | None:
    """Choose a legal attack by Pit formation role; depleted limited-use attacks are unavailable."""
    try:
        profiles = _attack_profiles(attacker, allowed_ids, kind)
        for target in target_order(attacker, setup, prefer_backline=prefer_backline):
            for attack in profiles:
                if attack_allowed_against(attack, attacker.combatant_id, target.state):
                    return target, attack, attack_distance(attacker, target, attack)
        return None
    except Exception as exc:
        logger.exception("Pit attack selection failed for %s.", attacker.combatant_id)
        raise RuntimeError("Pit attack selection could not be evaluated.") from exc


def choose_resource_backed_attack(
    attacker: EncounterCombatant,
    setup: EncounterSetup,
) -> tuple[EncounterCombatant, WeaponAttack, int] | None:
    ids = [
        attack.id for attack in [attacker.state.template.weapon_attack, *attacker.state.template.alternate_weapon_attacks]
        if attack.resource_id is not None
    ]
    return choose_attack(attacker, setup, ids) if ids else None


def choose_standard_attack(
    attacker: EncounterCombatant,
    setup: EncounterSetup,
) -> tuple[EncounterCombatant, WeaponAttack, int] | None:
    """Frontliners prefer melee; protected backliners prefer range; exposed backliners switch to melee when possible."""
    ids = [
        attacker.state.template.weapon_attack.id,
        *(attack.id for attack in attacker.state.template.alternate_weapon_attacks),
    ]
    if is_backline(attacker) and allied_frontline_active(attacker, setup):
        ranged = choose_attack(attacker, setup, ids, kind=WeaponAttackKind.RANGED)
        if ranged is not None:
            return ranged
    melee = choose_attack(attacker, setup, ids, kind=WeaponAttackKind.MELEE)
    if melee is not None:
        return melee
    return choose_attack(attacker, setup, ids, kind=WeaponAttackKind.RANGED)


def flexible_slot_has_both(attacker: EncounterCombatant, allowed_ids: list[str]) -> bool:
    profiles = _attack_profiles(attacker, allowed_ids, None)
    kinds = {attack.weapon.attack_kind for attack in profiles}
    return WeaponAttackKind.MELEE in kinds and WeaponAttackKind.RANGED in kinds
