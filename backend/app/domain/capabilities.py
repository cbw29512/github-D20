from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.actions import ConditionName, ConditionRemovalAction, HealingAction
from app.domain.capability_attacks import (
    AttackCapabilityDefinition,
    CapabilityActionSlot,
    MultiattackCapabilityDefinition,
    SaveCapabilityDefinition,
)
from app.domain.character_builds import AbilityScores
from app.domain.combatants import ResourceDefinition, VisualLoadout
from app.domain.movement import MovementModes
from app.domain.progression import ProgressionCombatFeatures
from app.domain.reactions import ParryReaction, RedirectAttackReaction
from app.domain.size import CreatureSize
from app.domain.spells import DefensiveSpellAction, SpellSaveAction
from app.domain.traits import CombatTrait
from app.domain.unarmed import UnarmedStrikeDamage
from app.domain.weapons import DamageType


class CombatantDefinition(BaseModel):
    schema_version: Literal[1] = 1
    id: str
    name: str
    archetype: str
    level: int | None = Field(default=None, ge=1, le=20)
    challenge_rating: str | None = None
    kind: Literal["character", "monster"]
    size: CreatureSize = CreatureSize.MEDIUM
    ability_scores: AbilityScores | None = None
    armor_class: int = Field(ge=1)
    max_hp: int = Field(ge=1)
    speed_ft: int = Field(ge=0)
    movement_modes: MovementModes | None = None
    initiative_bonus: int
    progression_features: ProgressionCombatFeatures = Field(default_factory=ProgressionCombatFeatures)
    attacks: list[AttackCapabilityDefinition] = Field(min_length=1)
    primary_attack_id: str
    unarmed_opportunity_attack: UnarmedStrikeDamage | None = None
    attack_action: MultiattackCapabilityDefinition | None = None
    save_actions: list[SaveCapabilityDefinition] = Field(default_factory=list)
    spell_save_actions: list[SpellSaveAction] = Field(default_factory=list)
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
    resources: list[ResourceDefinition] = Field(default_factory=list)
    visual: VisualLoadout
    source: str
    unsupported_capabilities: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_fighting_styles(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values
        normalized = dict(values)
        style = normalized.get("fighting_style")
        styles = normalized.get("fighting_styles") or []
        if not styles and style:
            normalized["fighting_styles"] = [style]
        elif styles and not style:
            normalized["fighting_style"] = styles[0]
        return normalized

    @model_validator(mode="after")
    def validate_references(self) -> "CombatantDefinition":
        attack_ids = {attack.id for attack in self.attacks}
        save_ids = {action.id for action in self.save_actions}
        resource_ids = {resource.id for resource in self.resources}
        if self.kind == "character" and self.ability_scores is None:
            raise ValueError("Character combatant definitions require ability scores.")
        if len(attack_ids) != len(self.attacks) or len(save_ids) != len(self.save_actions):
            raise ValueError("Capability ids must be unique within their action family.")
        if len(resource_ids) != len(self.resources):
            raise ValueError("Resource ids must be unique.")
        if self.primary_attack_id not in attack_ids:
            raise ValueError("primary_attack_id must reference a declared attack.")
        for attack in self.attacks:
            if attack.resource_id is not None and attack.resource_id not in resource_ids:
                raise ValueError(f"Attack {attack.id!r} references undeclared resource {attack.resource_id!r}.")
        for action in self.save_actions:
            if action.resource_id is not None and action.resource_id not in resource_ids:
                raise ValueError(f"Save action {action.id!r} references undeclared resource {action.resource_id!r}.")
        if self.attack_action:
            for slot in self.attack_action.slots:
                if not set(slot.attack_ids) <= attack_ids or not set(slot.save_action_ids) <= save_ids:
                    raise ValueError("Multiattack slot references an undeclared capability id.")
        return self
