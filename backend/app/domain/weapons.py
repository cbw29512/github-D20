from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.actions import AbilityName, HitControlEffect
from app.domain.hit_modifiers import HitModifierEffect
from app.domain.size import CreatureSize


class DamageType(StrEnum):
    ACID = "acid"
    BLUDGEONING = "bludgeoning"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    PIERCING = "piercing"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    THUNDER = "thunder"


class WeaponAttackKind(StrEnum):
    MELEE = "melee"
    RANGED = "ranged"


class ConditionalDamage(BaseModel):
    trigger: Literal["attack_advantage", "attacker_bloodied", "target_bloodied"]
    mode: Literal["add", "replace_weapon"] = "add"
    dice_count: int = Field(ge=1, le=20)
    dice_size: int = Field(ge=2, le=100)
    damage_bonus: int = 0
    damage_type: DamageType


class OnHitDamage(BaseModel):
    source: str
    dice_count: int = Field(ge=0, le=40)
    dice_size: int = Field(ge=2, le=100)
    damage_bonus: int = 0
    damage_type: DamageType

    @model_validator(mode="after")
    def _fixed_damage_requires_positive_amount(self) -> "OnHitDamage":
        if self.dice_count == 0 and self.damage_bonus <= 0:
            raise ValueError("A zero-die on-hit damage rider requires a positive fixed damage amount.")
        return self


class Weapon(BaseModel):
    id: str
    name: str
    attack_kind: WeaponAttackKind
    dice_count: int = Field(ge=0, le=20)
    dice_size: int = Field(ge=2, le=100)
    damage_type: DamageType
    animation: str
    reach_ft: int = Field(default=5, ge=0)
    normal_range_ft: int | None = Field(default=None, ge=1)
    long_range_ft: int | None = Field(default=None, ge=1)
    projectile: str | None = None
    mastery_property: str | None = None
    light: bool = False
    finesse: bool = False
    heavy: bool = False
    two_handed: bool = False
    versatile: bool = False


class WeaponAttack(BaseModel):
    id: str
    weapon: Weapon
    attack_bonus: int
    damage_bonus: int
    damage_die_minimum: int | None = Field(default=None, ge=2, le=100)
    attack_ability: AbilityName | None = None
    attack_ability_modifier: int | None = None
    fixed_damage: int | None = Field(default=None, ge=0)
    conditional_damage: list[ConditionalDamage] = Field(default_factory=list)
    on_hit_damage: list[OnHitDamage] = Field(default_factory=list)
    on_hit_modifier_effects: list[HitModifierEffect] = Field(default_factory=list)
    rage_eligible: bool = False
    sneak_attack_eligible: bool = False
    knocks_prone_max_size: CreatureSize | None = None
    control_effect: HitControlEffect | None = None
    forbid_target_grappled_by_self: bool = False
    resource_id: str | None = None
    resource_cost: int = Field(default=1, ge=1, le=20)
