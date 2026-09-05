from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.areas import AreaGeometry
from app.domain.size import CreatureSize

AbilityName = Literal["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
ActionCost = Literal["action", "bonus_action", "reaction"]
HealingTargetMode = Literal["self", "ally", "self_or_ally", "other"]
ConditionRemovalTargetMode = Literal["self", "ally", "self_or_ally"]
ConditionReactionTrigger = Literal["condition_applied_to_self", "condition_applied_to_ally"]
ConditionTiming = Literal["source_turn_start", "source_turn_end", "target_turn_start", "target_turn_end"]
DamageTypeName = Literal[
    "acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic",
    "piercing", "poison", "psychic", "radiant", "slashing", "thunder",
]
ConditionName = Literal[
    "blinded", "charmed", "deafened", "exhaustion", "frightened", "grappled",
    "incapacitated", "invisible", "paralyzed", "petrified", "poisoned", "prone",
    "restrained", "stunned", "unconscious",
]


class GrappleSource(BaseModel):
    source_id: str
    escape_dc: int = Field(ge=1, le=40)
    range_ft: int = Field(default=5, ge=0)
    restrains: bool = False


class HitControlEffect(BaseModel):
    max_target_size: CreatureSize | None = None
    grapple_escape_dc: int | None = Field(default=None, ge=1, le=40)
    restrains_while_grappled: bool = False
    condition_id: ConditionName | None = None
    expires_at_start_of_source_turn: bool = False
    expiry_timing: ConditionTiming | None = None
    repeat_save_ability: AbilityName | None = None
    repeat_save_dc: int | None = Field(default=None, ge=1, le=40)
    repeat_save_timing: ConditionTiming | None = None
    allowed_removal_action_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_condition_lifecycle(self) -> "HitControlEffect":
        repeat_fields = (self.repeat_save_ability, self.repeat_save_dc, self.repeat_save_timing)
        if any(item is not None for item in repeat_fields) and not all(item is not None for item in repeat_fields):
            raise ValueError("Repeat-save condition lifecycle requires ability, DC, and timing together.")
        if self.expires_at_start_of_source_turn and self.expiry_timing not in {None, "source_turn_start"}:
            raise ValueError("Legacy source-start expiry conflicts with explicit condition timing.")
        return self


class HealingAction(BaseModel):
    """A printed healing option with its actual action cost and target restrictions."""

    id: str
    name: str
    action_cost: ActionCost
    range_ft: int = Field(default=5, ge=0)
    target_mode: HealingTargetMode = "self_or_ally"
    dice_count: int = Field(default=0, ge=0, le=40)
    dice_size: int = Field(default=6, ge=2, le=100)
    healing_bonus: int = Field(default=0, ge=0)
    removable_conditions: list[ConditionName] = Field(default_factory=list)
    resource_id: str | None = None
    resource_cost: int = Field(default=1, ge=1, le=20)
    animation: str = "healing"


class ConditionRemovalAction(BaseModel):
    """A 2024 spell/feature that can legally end one or more named conditions."""

    id: str
    name: str
    action_cost: ActionCost
    range_ft: int = Field(default=5, ge=0)
    target_mode: ConditionRemovalTargetMode = "self_or_ally"
    removable_conditions: list[ConditionName] = Field(min_length=1)
    max_conditions_per_use: int = Field(default=1, ge=1, le=16)
    resource_costs: dict[str, int] = Field(default_factory=dict)
    resource_costs_per_condition: dict[str, int] = Field(default_factory=dict)
    reaction_trigger: ConditionReactionTrigger | None = None
    expends_spell_slot: bool = False
    animation: str = "condition-removal"

    @model_validator(mode="after")
    def validate_costs_and_timing(self) -> "ConditionRemovalAction":
        costs = [*self.resource_costs.values(), *self.resource_costs_per_condition.values()]
        if any(cost <= 0 for cost in costs):
            raise ValueError("Condition-removal resource costs must be positive.")
        if self.action_cost == "reaction" and self.reaction_trigger is None:
            raise ValueError("Reaction condition removal requires an explicit RAW trigger.")
        if self.action_cost != "reaction" and self.reaction_trigger is not None:
            raise ValueError("Only Reaction condition removal can define a reaction trigger.")
        resource_ids = {*self.resource_costs, *self.resource_costs_per_condition}
        has_spell_slot_resource = any(resource_id.startswith("spell-slot-") for resource_id in resource_ids)
        if has_spell_slot_resource != self.expends_spell_slot:
            raise ValueError("Spell-slot resources and expends_spell_slot must agree.")
        return self


class SavingThrowAction(BaseModel):
    id: str
    name: str
    save_ability: AbilityName
    dc: int = Field(ge=1, le=40)
    range_ft: int = Field(ge=0)
    target_max_size: CreatureSize | None = None
    area: AreaGeometry | None = None
    damage_dice_count: int = Field(default=0, ge=0, le=40)
    damage_dice_size: int = Field(default=6, ge=2, le=100)
    damage_bonus: int = 0
    damage_type: DamageTypeName | None = None
    success_damage: Literal["none", "half"] = "none"
    grapple_escape_dc: int | None = Field(default=None, ge=1, le=40)
    restrains_while_grappled: bool = False
    resource_id: str | None = None
    resource_cost: int = Field(default=1, ge=1, le=20)
    animation: str = "save-effect"


class AttackActionSlot(BaseModel):
    """One ordered weapon/save step inside an Attack action or Multiattack."""

    attack_ids: list[str] = Field(default_factory=list, max_length=16)
    save_action_ids: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def require_choice(self) -> "AttackActionSlot":
        if not self.attack_ids and not self.save_action_ids:
            raise ValueError("Attack-action slot must contain a weapon attack or saving-throw action.")
        return self


class AttackActionDefinition(BaseModel):
    """One or more ordered strikes/effects; only real Attack actions can trigger Light/Nick."""

    id: str
    name: str
    slots: list[AttackActionSlot] = Field(min_length=1, max_length=8)
    is_attack_action: bool = False
