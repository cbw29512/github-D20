from app.content.simple_damage_cantrips import build_simple_damage_cantrip
from app.domain.spells import SpellAttackAction, SpellSaveAction


def test_attack_cantrips_share_one_scaling_builder() -> None:
    cases = {
        "fire-bolt": (17, 4, 10, "fire", 120, "ranged"),
        "poison-spray": (11, 3, 12, "poison", 30, "ranged"),
        "ray-of-frost": (11, 3, 8, "cold", 60, "ranged"),
        "shocking-grasp": (17, 4, 8, "lightning", 5, "melee"),
        "starry-wisp": (5, 2, 8, "radiant", 60, "ranged"),
    }
    for spell_id, (level, dice_count, dice_size, damage_type, range_ft, attack_kind) in cases.items():
        spell = build_simple_damage_cantrip(
            spell_id, character_level=level, attack_bonus=11, save_dc=19,
        )
        assert isinstance(spell, SpellAttackAction)
        assert (spell.damage_dice_count, spell.damage_dice_size) == (dice_count, dice_size)
        assert (spell.damage_type, spell.range_ft, spell.attack_kind) == (damage_type, range_ft, attack_kind)
        assert spell.on_hit_modifier_effects == []


def test_save_cantrips_share_one_scaling_builder() -> None:
    cases = {
        "acid-splash": (5, 2, 6, "acid", "dexterity", 5),
        "mind-sliver": (11, 3, 6, "psychic", "intelligence", None),
        "sacred-flame": (20, 4, 8, "radiant", "dexterity", None),
        "vicious-mockery": (17, 4, 6, "psychic", "wisdom", None),
    }
    for spell_id, (level, dice_count, dice_size, damage_type, save_ability, radius) in cases.items():
        spell = build_simple_damage_cantrip(
            spell_id, character_level=level, attack_bonus=11, save_dc=19,
        )
        assert isinstance(spell, SpellSaveAction)
        assert (spell.damage_dice_count, spell.damage_dice_size) == (dice_count, dice_size)
        assert (spell.damage_type, spell.save_ability, spell.area_radius_ft) == (damage_type, save_ability, radius)
        assert spell.success_damage == "none"


def test_unmodeled_damage_cantrip_fails_closed() -> None:
    try:
        build_simple_damage_cantrip(
            "produce-flame", character_level=20, attack_bonus=11, save_dc=19,
        )
    except ValueError as exc:
        assert "Unsupported simple damage cantrip" in str(exc)
    else:
        raise AssertionError("produce-flame must fail closed until its damage action is audited.")
