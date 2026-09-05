from __future__ import annotations

import logging
from typing import Any

from app.combat.charge import charge_profile_for_attack_id
from app.domain.models import CombatantTemplate, WeaponAttack
from app.domain.traits import CombatTrait

logger = logging.getLogger(__name__)


def _value(item: Any) -> Any:
    return getattr(item, "value", item)


def _control(effect: Any) -> dict[str, Any] | None:
    if effect is None:
        return None
    row: dict[str, Any] = {}
    if effect.max_target_size:
        row["maxTargetSize"] = _value(effect.max_target_size)
    if effect.grapple_escape_dc is not None:
        row["grappleEscapeDc"] = effect.grapple_escape_dc
    if effect.restrains_while_grappled:
        row["restrainsWhileGrappled"] = True
    if effect.condition_id:
        row["conditionId"] = effect.condition_id
        if effect.expires_at_start_of_source_turn:
            row["expiresAtStartOfSourceTurn"] = True
        if effect.expiry_timing:
            row["expiryTiming"] = effect.expiry_timing
        if effect.repeat_save_ability:
            row["repeatSaveAbility"] = effect.repeat_save_ability
            row["repeatSaveDc"] = effect.repeat_save_dc
            row["repeatSaveTiming"] = effect.repeat_save_timing
        if effect.allowed_removal_action_ids:
            row["allowedRemovalActionIds"] = list(effect.allowed_removal_action_ids)
    return row or None


def _hit_modifier(effect: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"kind": effect.kind}
    if effect.flat_bonus:
        row["flatBonus"] = effect.flat_bonus
    if effect.consume_on_attack_against:
        row["consumeOnAttackAgainst"] = True
    if effect.expires_at_start_of_source_turn:
        row["expiresAtStartOfSourceTurn"] = True
    if effect.expires_at_end_of_target_turn:
        row["expiresAtEndOfTargetTurn"] = True
    return row


def attack_row(attack: WeaponAttack, traits: set[str]) -> dict[str, Any]:
    try:
        weapon = attack.weapon
        row: dict[str, Any] = {
            "id": attack.id, "name": weapon.name, "kind": weapon.attack_kind.value,
            "bonus": attack.attack_bonus, "diceCount": weapon.dice_count, "diceSize": weapon.dice_size,
            "damageBonus": attack.damage_bonus, "damageType": weapon.damage_type.value,
            "reach": weapon.reach_ft, "animation": weapon.animation,
        }
        if weapon.normal_range_ft is not None:
            row.update(normal=weapon.normal_range_ft, long=weapon.long_range_ft, projectile=weapon.projectile)
        if attack.fixed_damage is not None:
            row["fixedDamage"] = attack.fixed_damage
        if attack.rage_eligible:
            row["rageEligible"] = True
        if attack.knocks_prone_max_size is not None:
            row["proneMaxSize"] = attack.knocks_prone_max_size.value
        if attack.forbid_target_grappled_by_self:
            row["forbidSelfGrappledTarget"] = True
        if attack.on_hit_damage:
            row["onHitDamage"] = [
                {"source": part.source, "diceCount": part.dice_count, "diceSize": part.dice_size,
                 "damageBonus": part.damage_bonus, "damageType": part.damage_type.value}
                for part in attack.on_hit_damage
            ]
        if attack.on_hit_modifier_effects:
            row["onHitModifiers"] = [_hit_modifier(effect) for effect in attack.on_hit_modifier_effects]
        if attack.conditional_damage:
            if len(attack.conditional_damage) != 1:
                raise ValueError(f"Browser supports one conditional damage rider on {attack.id}.")
            conditional = attack.conditional_damage[0]
            legacy = (
                conditional.trigger == "attack_advantage" and conditional.mode == "add"
                and conditional.damage_bonus == 0 and conditional.damage_type == weapon.damage_type
            )
            if legacy:
                row["conditionalAdvantage"] = [conditional.dice_count, conditional.dice_size]
            else:
                row["conditionalDamage"] = {
                    "trigger": conditional.trigger, "mode": conditional.mode,
                    "diceCount": conditional.dice_count, "diceSize": conditional.dice_size,
                    "damageBonus": conditional.damage_bonus, "damageType": conditional.damage_type.value,
                }
        control = _control(attack.control_effect)
        if control:
            row["controlEffect"] = control
        if CombatTrait.CHARGE.value in traits:
            profile = charge_profile_for_attack_id(attack.id)
            if profile:
                charge: dict[str, Any] = {"minimumMove": profile.minimum_move_ft}
                if profile.prone_max_target_size is not None:
                    charge["proneMaxSize"] = profile.prone_max_target_size.value
                if profile.max_target_size is not None and profile.max_target_size != profile.prone_max_target_size:
                    charge["targetMaxSize"] = profile.max_target_size.value
                if profile.bonus_damage is not None:
                    charge.update(
                        diceCount=profile.bonus_damage.dice_count,
                        diceSize=profile.bonus_damage.dice_size,
                        damageType=profile.bonus_damage.damage_type.value,
                    )
                if profile.replacement_damage is not None:
                    replacement = profile.replacement_damage
                    charge["replacementDamage"] = {
                        "diceCount": replacement.dice_count, "diceSize": replacement.dice_size,
                        "damageBonus": replacement.damage_bonus, "damageType": replacement.damage_type.value,
                    }
                if profile.follow_up_attack_id:
                    charge["followUpAttackId"] = profile.follow_up_attack_id
                row["charge"] = charge
        return row
    except Exception:
        logger.exception("Failed to serialize attack %s for browser runtime.", attack.id)
        raise


def _save(action: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": action.id, "name": action.name, "saveAbility": action.save_ability, "dc": action.dc,
        "range": action.range_ft, "damageDiceCount": action.damage_dice_count,
        "damageDiceSize": action.damage_dice_size, "damageBonus": action.damage_bonus,
        "damageType": action.damage_type, "successDamage": action.success_damage, "animation": action.animation,
    }
    if action.target_max_size:
        row["targetMaxSize"] = _value(action.target_max_size)
    if action.grapple_escape_dc is not None:
        row["grappleEscapeDc"] = action.grapple_escape_dc
    if action.restrains_while_grappled:
        row["restrainsWhileGrappled"] = True
    if action.resource_id:
        row["resourceId"] = action.resource_id
        row["resourceCost"] = action.resource_cost
    return row


def _spell(action: Any) -> dict[str, Any]:
    row = {
        "id": action.id, "name": action.name, "level": action.level, "actionCost": action.action_cost,
        "range": action.range_ft, "saveAbility": action.save_ability, "dc": action.dc,
        "damageDiceCount": action.damage_dice_count, "damageDiceSize": action.damage_dice_size,
        "damageBonus": action.damage_bonus, "damageType": action.damage_type,
        "successDamage": action.success_damage, "upcastDicePerLevel": action.upcast_dice_per_level,
        "concentration": action.concentration, "animation": action.animation,
    }
    if action.area_radius_ft is not None:
        row["areaRadius"] = action.area_radius_ft
    return row


def _modifier_effect(effect: Any) -> dict[str, Any]:
    row = {
        "kind": effect.kind, "flatBonus": effect.flat_bonus, "diceCount": effect.dice_count,
        "diceSize": effect.dice_size, "damageType": effect.damage_type,
    }
    if effect.consume_on_attack_against:
        row["consumeOnAttackAgainst"] = True
    if effect.expires_after_source_turns is not None:
        row["expiresAfterSourceTurns"] = effect.expires_after_source_turns
    return row


def _spell_attack(action: Any) -> dict[str, Any]:
    row = {
        "id": action.id, "name": action.name, "level": action.level, "actionCost": action.action_cost,
        "range": action.range_ft, "attackBonus": action.attack_bonus,
        "damageDiceCount": action.damage_dice_count, "damageDiceSize": action.damage_dice_size,
        "damageBonus": action.damage_bonus, "damageType": action.damage_type,
        "onHitModifierEffects": [_modifier_effect(effect) for effect in action.on_hit_modifier_effects],
        "animation": action.animation,
    }
    if action.source:
        row["source"] = action.source
    return row


def _healing(action: Any) -> dict[str, Any]:
    return {
        "id": action.id, "name": action.name, "actionCost": action.action_cost,
        "range": action.range_ft, "targetMode": action.target_mode,
        "diceCount": action.dice_count, "diceSize": action.dice_size,
        "healingBonus": action.healing_bonus, "resourceId": action.resource_id,
        "resourceCost": action.resource_cost, "animation": action.animation,
    }


def defense_row(action: Any) -> dict[str, Any]:
    row = {
        "id": action.id, "name": action.name, "level": action.level, "actionCost": action.action_cost,
        "range": action.range_ft, "durationMinutes": action.duration_minutes,
        "targetPolicy": action.target_policy, "targetCount": action.target_count,
        "temporaryHp": action.temporary_hp,
        "temporaryHpPerSlotAbove": action.temporary_hp_per_slot_above,
        "damageResistances": list(action.damage_resistances),
        "modifierEffects": [_modifier_effect(effect) for effect in action.modifier_effects],
        "concentration": action.concentration, "priority": action.priority, "animation": action.animation,
    }
    if action.max_hp_increase:
        row["maxHpIncrease"] = action.max_hp_increase
    if action.current_hp_increase:
        row["currentHpIncrease"] = action.current_hp_increase
    if action.source:
        row["source"] = action.source
    return row


def _removal(action: Any) -> dict[str, Any]:
    row = {
        "id": action.id, "name": action.name, "actionCost": action.action_cost, "range": action.range_ft,
        "targetMode": action.target_mode, "removableConditions": list(action.removable_conditions),
        "maxConditionsPerUse": action.max_conditions_per_use, "resourceCosts": dict(action.resource_costs),
        "resourceCostsPerCondition": dict(action.resource_costs_per_condition),
        "expendsSpellSlot": action.expends_spell_slot, "animation": action.animation,
    }
    if action.reaction_trigger:
        row["reactionTrigger"] = action.reaction_trigger
    return row


def _progression_features(template: CombatantTemplate) -> dict[str, Any]:
    features = template.progression_features
    row: dict[str, Any] = {}
    if features.critical_hit_minimum != 20:
        row["critical_hit_minimum"] = features.critical_hit_minimum
    if features.initiative_advantage:
        row["initiative_advantage"] = True
    if features.athletics_advantage:
        row["athletics_advantage"] = True
    if features.critical_move_fraction:
        row["critical_move_fraction"] = features.critical_move_fraction
    return row


def _resource_recharges(template: CombatantTemplate) -> dict[str, dict[str, Any]]:
    return {
        item.id: {
            "name": item.name, "minimum": item.recharge.minimum,
            "maximum": item.recharge.maximum, "dieSize": item.recharge.die_size,
        }
        for item in template.resources if item.recharge is not None
    }


def template_row(template: CombatantTemplate) -> dict[str, Any]:
    try:
        traits = {item.value for item in template.combat_traits}
        attacks = [template.weapon_attack, *template.alternate_weapon_attacks]
        row: dict[str, Any] = {
            "id": template.id, "name": template.name, "archetype": template.archetype,
            "level": template.level, "challenge_rating": template.challenge_rating, "kind": template.kind,
            "size": template.size.value, "armor_class": template.armor_class, "max_hp": template.max_hp,
            "speed_ft": template.speed_ft, "movement_modes": template.movement_modes.model_dump(),
            "initiative_bonus": template.initiative_bonus,
            "saving_throw_bonuses": template.saving_throw_bonuses, "skill_bonuses": template.skill_bonuses,
            "attacks": [attack_row(item, traits) for item in attacks], "primary_attack_id": template.weapon_attack.id,
            "saving_throw_actions": [_save(item) for item in template.saving_throw_actions],
            "traits": sorted(traits), "resources": {item.id: item.max_uses for item in template.resources},
            "damage_resistances": [item.value for item in template.damage_resistances],
            "damage_vulnerabilities": [item.value for item in template.damage_vulnerabilities],
            "damage_immunities": [item.value for item in template.damage_immunities],
            "condition_immunities": list(template.condition_immunities),
            "visual": {"armor": template.visual.armor, "main_hand": template.visual.main_hand,
                       "off_hand": template.visual.off_hand, "body_style": template.visual.body_style},
            "source": template.source, **_progression_features(template),
        }
        recharge = _resource_recharges(template)
        if recharge:
            row["resource_recharges"] = recharge
        if template.kind == "monster":
            row["source_trait_names"] = list(template.source_trait_names)
            row["source_reaction_names"] = list(template.source_reaction_names)
            row["source_bonus_action_names"] = list(template.source_bonus_action_names)
            row["source_limited_use_names"] = list(template.source_limited_use_names)
            row["source_legendary_action_names"] = list(template.source_legendary_action_names)
            row["source_spellcasting_fingerprint"] = template.source_spellcasting_fingerprint
        if template.parry_reaction:
            row["parry_reaction"] = {"ac_bonus": template.parry_reaction.ac_bonus}
        if template.redirect_attack_reaction:
            row["redirect_attack_reaction"] = {
                "ally_range_ft": template.redirect_attack_reaction.ally_range_ft,
                "ally_max_size": template.redirect_attack_reaction.ally_max_size.value,
            }
        if template.spell_save_actions:
            row["spell_save_actions"] = [_spell(item) for item in template.spell_save_actions]
        if template.spell_attack_actions:
            row["spell_attack_actions"] = [_spell_attack(item) for item in template.spell_attack_actions]
        if template.defensive_spell_actions:
            row["defensive_spell_actions"] = [defense_row(item) for item in template.defensive_spell_actions]
        if template.healing_actions:
            row["healingActions"] = [_healing(item) for item in template.healing_actions]
        if template.condition_removal_actions:
            row["condition_removal_actions"] = [_removal(item) for item in template.condition_removal_actions]
        if template.attack_action:
            row["attack_action"] = {"id": template.attack_action.id, "name": template.attack_action.name, "slots": [
                {"attackIds": slot.attack_ids, "saveActionIds": slot.save_action_ids}
                for slot in template.attack_action.slots
            ]}
        return row
    except Exception:
        logger.exception("Failed to serialize combatant template %s.", template.id)
        raise
