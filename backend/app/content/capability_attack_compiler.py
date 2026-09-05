from __future__ import annotations

from app.domain.actions import HitControlEffect
from app.domain.capabilities import AttackCapabilityDefinition
from app.domain.capability_effects import (
    ConditionEffectDefinition,
    DamageEffectDefinition,
    GrappleEffectDefinition,
    ProneEffectDefinition,
)
from app.domain.hit_modifiers import HitModifierEffect
from app.domain.models import ConditionalDamage, OnHitDamage, Weapon, WeaponAttack


class UnsupportedCapabilityError(ValueError):
    pass


def _compile_control(effect: GrappleEffectDefinition | ConditionEffectDefinition) -> HitControlEffect:
    if isinstance(effect, GrappleEffectDefinition):
        return HitControlEffect(
            max_target_size=effect.max_target_size,
            grapple_escape_dc=effect.escape_dc,
            restrains_while_grappled=effect.restrains,
        )
    return HitControlEffect(
        max_target_size=effect.max_target_size,
        condition_id=effect.condition,
        expires_at_start_of_source_turn=effect.expires_at_start_of_source_turn,
        expiry_timing=effect.expiry_timing,
        repeat_save_ability=effect.repeat_save_ability,
        repeat_save_dc=effect.repeat_save_dc,
        repeat_save_timing=effect.repeat_save_timing,
        allowed_removal_action_ids=effect.allowed_removal_action_ids,
    )


def compile_attack(definition: AttackCapabilityDefinition) -> WeaponAttack:
    damage = definition.damage
    weapon = Weapon(
        id=definition.weapon_id or definition.id,
        name=definition.name,
        attack_kind=definition.attack_kind,
        dice_count=damage.count if damage else 0,
        dice_size=damage.size if damage else 2,
        damage_type=definition.damage_type,
        animation=definition.animation,
        reach_ft=definition.reach_ft,
        normal_range_ft=definition.normal_range_ft,
        long_range_ft=definition.long_range_ft,
        projectile=definition.projectile,
        mastery_property=definition.mastery_property,
        light=definition.light,
        finesse=definition.finesse,
        heavy=definition.heavy,
        two_handed=definition.two_handed,
        versatile=definition.versatile,
    )
    on_hit: list[OnHitDamage] = []
    on_hit_modifiers: list[HitModifierEffect] = []
    conditional: list[ConditionalDamage] = []
    prone_size = None
    control = None
    for effect in definition.effects:
        if isinstance(effect, DamageEffectDefinition):
            if effect.trigger == "on_hit":
                on_hit.append(OnHitDamage(
                    source=effect.source,
                    dice_count=effect.dice.count,
                    dice_size=effect.dice.size,
                    damage_bonus=effect.dice.bonus,
                    damage_type=effect.damage_type,
                ))
            else:
                conditional.append(ConditionalDamage(
                    trigger=effect.trigger,
                    mode=effect.mode,
                    dice_count=effect.dice.count,
                    dice_size=effect.dice.size,
                    damage_bonus=effect.dice.bonus,
                    damage_type=effect.damage_type,
                ))
        elif isinstance(effect, ProneEffectDefinition):
            prone_size = effect.max_target_size
        elif isinstance(effect, HitModifierEffect):
            on_hit_modifiers.append(effect)
        elif isinstance(effect, (GrappleEffectDefinition, ConditionEffectDefinition)):
            control = _compile_control(effect)
        else:
            raise UnsupportedCapabilityError(f"Unsupported attack effect: {effect!r}")
    return WeaponAttack(
        id=definition.id,
        weapon=weapon,
        attack_bonus=definition.attack_bonus,
        damage_bonus=damage.bonus if damage else 0,
        attack_ability=definition.attack_ability,
        attack_ability_modifier=definition.attack_ability_modifier,
        rage_eligible=definition.rage_eligible,
        fixed_damage=definition.fixed_damage,
        conditional_damage=conditional,
        on_hit_damage=on_hit,
        on_hit_modifier_effects=on_hit_modifiers,
        knocks_prone_max_size=prone_size,
        control_effect=control,
        forbid_target_grappled_by_self=definition.forbid_target_grappled_by_self,
        resource_id=definition.resource_id,
        resource_cost=definition.resource_cost or 1,
    )
