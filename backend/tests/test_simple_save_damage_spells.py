from app.content.simple_save_damage_spells import build_simple_save_damage_spell


def test_fireball_is_data_only_save_half_area_damage() -> None:
    spell = build_simple_save_damage_spell("fireball", 16)
    assert (spell.level, spell.range_ft, spell.area_radius_ft) == (3, 150, 20)
    assert (spell.save_ability, spell.dc) == ("dexterity", 16)
    assert (spell.damage_dice_count, spell.damage_dice_size, spell.damage_type) == (8, 6, "fire")
    assert (spell.success_damage, spell.upcast_dice_per_level) == ("half", 1)


def test_simple_save_damage_family_covers_single_target_and_area_spells() -> None:
    shatter = build_simple_save_damage_spell("shatter", 15)
    blight = build_simple_save_damage_spell("blight", 17)
    circle = build_simple_save_damage_spell("circle-of-death", 18)
    finger = build_simple_save_damage_spell("finger-of-death", 18)
    assert (shatter.area_radius_ft, shatter.damage_type) == (10, "thunder")
    assert (blight.area_radius_ft, blight.damage_dice_count) == (None, 8)
    assert (circle.area_radius_ft, circle.damage_dice_count, circle.upcast_dice_per_level) == (60, 8, 2)
    assert (finger.damage_dice_count, finger.damage_dice_size, finger.damage_bonus) == (7, 8, 30)


def test_disintegrate_uses_save_for_zero_damage_on_success() -> None:
    spell = build_simple_save_damage_spell("disintegrate", 19)
    assert (spell.level, spell.save_ability, spell.success_damage) == (6, "dexterity", "none")
    assert (spell.damage_dice_count, spell.damage_dice_size, spell.damage_bonus) == (10, 6, 40)
    assert spell.damage_type == "force"


def test_unknown_spell_fails_closed() -> None:
    for spell_id in ("ice-storm", "chain-lightning", "sunburst"):
        try:
            build_simple_save_damage_spell(spell_id, 16)
        except ValueError as exc:
            assert "Unsupported simple save-damage spell" in str(exc)
        else:
            raise AssertionError(f"{spell_id} must fail closed until its full mechanic is modeled.")
