from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domain.actions import AbilityName, DamageTypeName
from app.domain.spells import SpellSaveAction


@dataclass(frozen=True)
class SaveDamageSpellSpec:
    id: str
    name: str
    level: int
    range_ft: int
    save_ability: AbilityName
    dice_count: int
    dice_size: int
    damage_type: DamageTypeName
    success_damage: Literal["none", "half"] = "half"
    area_radius_ft: int | None = None
    damage_bonus: int = 0
    upcast_dice_per_level: int = 0


SIMPLE_SAVE_DAMAGE_SPELLS = {
    "shatter": SaveDamageSpellSpec(
        "shatter", "Shatter", 2, 60, "constitution", 3, 8, "thunder",
        area_radius_ft=10, upcast_dice_per_level=1,
    ),
    "fireball": SaveDamageSpellSpec(
        "fireball", "Fireball", 3, 150, "dexterity", 8, 6, "fire",
        area_radius_ft=20, upcast_dice_per_level=1,
    ),
    "blight": SaveDamageSpellSpec(
        "blight", "Blight", 4, 30, "constitution", 8, 8, "necrotic",
        upcast_dice_per_level=1,
    ),
    "circle-of-death": SaveDamageSpellSpec(
        "circle-of-death", "Circle of Death", 6, 150, "constitution", 8, 8, "necrotic",
        area_radius_ft=60, upcast_dice_per_level=2,
    ),
    "disintegrate": SaveDamageSpellSpec(
        "disintegrate", "Disintegrate", 6, 60, "dexterity", 10, 6, "force",
        success_damage="none", damage_bonus=40,
    ),
    "finger-of-death": SaveDamageSpellSpec(
        "finger-of-death", "Finger of Death", 7, 60, "constitution", 7, 8, "necrotic",
        damage_bonus=30,
    ),
}


def build_simple_save_damage_spell(spell_id: str, save_dc: int) -> SpellSaveAction:
    try:
        spec = SIMPLE_SAVE_DAMAGE_SPELLS[spell_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported simple save-damage spell: {spell_id}.") from exc
    return SpellSaveAction(
        id=spec.id,
        name=spec.name,
        level=spec.level,
        range_ft=spec.range_ft,
        area_radius_ft=spec.area_radius_ft,
        save_ability=spec.save_ability,
        dc=save_dc,
        damage_dice_count=spec.dice_count,
        damage_dice_size=spec.dice_size,
        damage_bonus=spec.damage_bonus,
        damage_type=spec.damage_type,
        success_damage=spec.success_damage,
        upcast_dice_per_level=spec.upcast_dice_per_level,
        animation=spec.id,
    )
