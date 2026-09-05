from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.actions import AbilityName
from app.domain.areas import AreaGeometry
from app.domain.capability_effects import AttackEffectDefinition, DiceSpec, GrappleEffectDefinition
from app.domain.size import CreatureSize
from app.domain.weapons import DamageType, WeaponAttackKind


class AttackCapabilityDefinition(BaseModel):
    id: str
    name: str
    weapon_id: str | None = None
    attack_kind: WeaponAttackKind
    attack_bonus: int
    damage: DiceSpec | None = None
    fixed_damage: int | None = Field(default=None, ge=0)
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
    attack_ability: AbilityName | None = None
    attack_ability_modifier: int | None = None
    rage_eligible: bool = False
    effects: list[AttackEffectDefinition] = Field(default_factory=list)
    forbid_target_grappled_by_self: bool = False
    resource_id: str | None = None
    resource_cost: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def validate_attack_shape(self) -> "AttackCapabilityDefinition":
        if (self.damage is None) == (self.fixed_damage is None):
            raise ValueError("Attack must declare exactly one of damage or fixed_damage.")
        if self.attack_kind == WeaponAttackKind.RANGED and (
            self.normal_range_ft is None or self.long_range_ft is None
        ):
            raise ValueError("Ranged attack requires normal and long range.")
        if self.attack_ability_modifier is not None and self.attack_ability is None:
            raise ValueError("Attack ability modifier requires an explicit attack ability.")
        if self.resource_id is None and self.resource_cost is not None:
            raise ValueError("Attack resource cost requires a resource id.")
        if self.resource_id is not None and self.resource_cost is None:
            raise ValueError("Resource-backed attack requires an explicit resource cost.")
        control_count = sum(effect.kind in {"grapple", "condition"} for effect in self.effects)
        if control_count > 1:
            raise ValueError("Current runtime supports one persistent control rider per attack.")
        return self


class SaveCapabilityDefinition(BaseModel):
    id: str
    name: str
    save_ability: Literal["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    dc: int = Field(ge=1, le=40)
    range_ft: int = Field(ge=0)
    target_max_size: CreatureSize | None = None
    area: AreaGeometry | None = None
    damage: DiceSpec | None = None
    damage_type: DamageType | None = None
    success_damage: Literal["none", "half"] = "none"
    grapple: GrappleEffectDefinition | None = None
    resource_id: str | None = None
    resource_cost: int | None = Field(default=None, ge=1, le=20)
    animation: str = "save-effect"

    @model_validator(mode="after")
    def validate_damage(self) -> "SaveCapabilityDefinition":
        if (self.damage is None) != (self.damage_type is None):
            raise ValueError("Save damage dice and damage type must be declared together.")
        if self.resource_id is None and self.resource_cost is not None:
            raise ValueError("Save resource cost requires a resource id.")
        if self.grapple and self.grapple.max_target_size and self.target_max_size:
            if self.grapple.max_target_size != self.target_max_size:
                raise ValueError("Save target size and grapple target size cannot disagree.")
        return self


class CapabilityActionSlot(BaseModel):
    attack_ids: list[str] = Field(default_factory=list, max_length=16)
    save_action_ids: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def require_choice(self) -> "CapabilityActionSlot":
        if not self.attack_ids and not self.save_action_ids:
            raise ValueError("Attack-action slot requires an attack or save action.")
        return self


class MultiattackCapabilityDefinition(BaseModel):
    id: str
    name: str = "Multiattack"
    is_attack_action: bool = False
    slots: list[CapabilityActionSlot] = Field(min_length=1, max_length=8)
