from __future__ import annotations

from app.domain.actions import HealingAction


def _spell_heal(
    spell_id: str, name: str, action_cost: str, range_ft: int,
    dice_count: int, dice_size: int, spellcasting_modifier: int, extra_healing_bonus: int = 0,
) -> HealingAction:
    if spellcasting_modifier < 0 or extra_healing_bonus < 0:
        raise ValueError(f"Certified {name} requires nonnegative healing modifiers.")
    return HealingAction(
        id=spell_id, name=name, action_cost=action_cost, range_ft=range_ft,
        target_mode="self_or_ally", dice_count=dice_count, dice_size=dice_size,
        healing_bonus=spellcasting_modifier + extra_healing_bonus,
        resource_id="spell-slot-1", resource_cost=1, animation="healing",
    )


def build_cure_wounds(spellcasting_modifier: int, extra_healing_bonus: int = 0) -> HealingAction:
    """Printed-level 2024 Cure Wounds; higher-slot casting remains deliberately deferred."""
    return _spell_heal(
        "cure-wounds", "Cure Wounds", "action", 5, 2, 8,
        spellcasting_modifier, extra_healing_bonus,
    )


def build_healing_word(spellcasting_modifier: int, extra_healing_bonus: int = 0) -> HealingAction:
    """Printed-level 2024 Healing Word; higher-slot casting remains deliberately deferred."""
    return _spell_heal(
        "healing-word", "Healing Word", "bonus_action", 60, 2, 4,
        spellcasting_modifier, extra_healing_bonus,
    )


def build_heal() -> HealingAction:
    """Printed-level 2024 Heal: 70 HP and Blinded/Deafened/Poisoned removal."""
    return HealingAction(
        id="heal", name="Heal", action_cost="action", range_ft=60,
        target_mode="self_or_ally", healing_bonus=70,
        removable_conditions=["blinded", "deafened", "poisoned"],
        resource_id="spell-slot-6", resource_cost=1, animation="heal",
    )
