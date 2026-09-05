from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.actions import AttackActionDefinition, ConditionName, ConditionRemovalAction, HealingAction, SavingThrowAction
from app.domain.character_builds import AbilityScores
from app.domain.movement import MovementModes
from app.domain.progression import ProgressionCombatFeatures
from app.domain.reactions import ParryReaction, RedirectAttackReaction
from app.domain.size import CreatureSize
from app.domain.spells import DefensiveSpellAction, SpellAttackAction, SpellSaveAction
from app.domain.traits import CombatTrait
from app.domain.unarmed import UnarmedStrikeDamage
from app.domain.weapons import (
    ConditionalDamage,
    DamageType,
    OnHitDamage,
    Weapon,
    WeaponAttack,
    WeaponAttackKind,
)


class VisualLoadout(BaseModel):
    armor: str
    main_hand: str
    off_hand: str | None = None
    body_style: str = "humanoid"


class RechargeDefinition(BaseModel):
    minimum: int = Field(ge=1)
    maximum: int = Field(default=6, ge=1)
    die_size: int = Field(default=6, ge=2)

    @model_validator(mode="after")
    def validate_range(self) -> "RechargeDefinition":
        if self.minimum > self.maximum or self.maximum > self.die_size:
            raise ValueError("Recharge range must fit within the recharge die.")
        return self


class ResourceDefinition(BaseModel):
    id: str
    name: str
    max_uses: int = Field(ge=0)
    recharge: RechargeDefinition | None = None


class CombatantTemplate(BaseModel):
    id: str
    name: str
    archetype: str
    level: int | None = Field(default=None, ge=1, le=20)
    challenge_rating: str | None = None
    kind: Literal["character", "monster"]
    creature_type: str | None = None
    size: CreatureSize = CreatureSize.MEDIUM
    ability_scores: AbilityScores | None = None
    armor_class: int = Field(ge=1)
    max_hp: int = Field(ge=1)
    speed_ft: int = Field(ge=0)
    movement_modes: MovementModes
    initiative_bonus: int
    progression_features: ProgressionCombatFeatures = Field(default_factory=ProgressionCombatFeatures)
    weapon_attack: WeaponAttack
    alternate_weapon_attacks: list[WeaponAttack] = Field(default_factory=list)
    unarmed_opportunity_attack: UnarmedStrikeDamage | None = None
    attack_action: AttackActionDefinition | None = None
    saving_throw_actions: list[SavingThrowAction] = Field(default_factory=list)
    spell_save_actions: list[SpellSaveAction] = Field(default_factory=list)
    spell_attack_actions: list[SpellAttackAction] = Field(default_factory=list)
    defensive_spell_actions: list[DefensiveSpellAction] = Field(default_factory=list)
    healing_actions: list[HealingAction] = Field(default_factory=list)
    condition_removal_actions: list[ConditionRemovalAction] = Field(default_factory=list)
    saving_throw_bonuses: dict[str, int] = Field(default_factory=dict)
    skill_bonuses: dict[str, int] = Field(default_factory=dict)
    combat_traits: list[CombatTrait] = Field(default_factory=list)
    source_trait_names: list[str] = Field(default_factory=list)
    source_reaction_names: list[str] = Field(default_factory=list)
    source_bonus_action_names: list[str] = Field(default_factory=list)
    source_limited_use_names: list[str] = Field(default_factory=list)
    source_legendary_action_names: list[str] = Field(default_factory=list)
    source_spellcasting_fingerprint: str | None = None
    parry_reaction: ParryReaction | None = None
    redirect_attack_reaction: RedirectAttackReaction | None = None
    fighting_style: str | None = None
    fighting_styles: list[str] = Field(default_factory=list)
    weapon_masteries: list[str] = Field(default_factory=list)
    damage_resistances: list[DamageType] = Field(default_factory=list)
    damage_vulnerabilities: list[DamageType] = Field(default_factory=list)
    damage_immunities: list[DamageType] = Field(default_factory=list)
    condition_immunities: list[ConditionName] = Field(default_factory=list)
    wearing_heavy_armor: bool = False
    rage_damage_bonus: int = Field(default=0, ge=0, le=10)
    visual: VisualLoadout
    resources: list[ResourceDefinition] = Field(default_factory=list)
    source: str

    @model_validator(mode="before")
    @classmethod
    def _normalize_compatibility_fields(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values
        normalized = dict(values)
        if "movement_modes" not in normalized and "speed_ft" in normalized:
            normalized["movement_modes"] = {"walk_ft": normalized["speed_ft"]}
        style = normalized.get("fighting_style")
        styles = normalized.get("fighting_styles")
        if styles is None:
            styles = []
        if not styles and style:
            normalized["fighting_styles"] = [style]
        elif styles and not style:
            normalized["fighting_style"] = styles[0]
        return normalized
