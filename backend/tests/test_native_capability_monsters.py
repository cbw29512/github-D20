import pytest

from app.content.capability_registry import (
    build_combatant_from_capabilities,
    get_capability_definition,
    load_capability_definitions,
    merge_capability_definitions,
)
from app.content.legacy_monster_roster import build_legacy_monster_templates
from app.content.monster_catalog import load_monster_rows
from app.content.monster_save_math_source_audit import save_math_issues
from app.content.monster_source_audit import audit_monster_source
from app.content.roster import build_arena_roster
from app.domain.traits import CombatTrait


def _native_monsters() -> dict[str, str]:
    legacy_ids = {monster.id for monster in build_legacy_monster_templates()}
    return {
        definition.id: definition.name
        for definition in load_capability_definitions().values()
        if definition.kind == "monster" and definition.id not in legacy_ids
    }


def test_native_monsters_are_not_legacy_builder_outputs() -> None:
    legacy_ids = {monster.id for monster in build_legacy_monster_templates()}
    assert set(_native_monsters()).isdisjoint(legacy_ids)


def test_native_definitions_extend_production_roster_without_replacing_legacy_ids() -> None:
    legacy = build_legacy_monster_templates()
    native = _native_monsters()
    production = build_arena_roster().monsters
    assert len(production) == len(legacy) + len(native)
    assert [monster.id for monster in production[-len(native):]] == list(native)


def test_native_registry_rejects_cross_layer_duplicate_ids() -> None:
    definition = get_capability_definition("srd-swarm-of-insects")
    with pytest.raises(ValueError, match="ids overlap"):
        merge_capability_definitions({definition.id: definition}, {definition.id: definition})


def test_native_monsters_compile_and_pass_full_srd_source_audit() -> None:
    rows = {str(row["name"]): row for row in load_monster_rows()}
    runtime = {monster.id: monster for monster in build_arena_roster().monsters}
    for template_id, source_name in _native_monsters().items():
        assert get_capability_definition(template_id).kind == "monster"
        assert audit_monster_source(runtime[template_id], rows[source_name]) == []


def test_srd_long_wide_line_wording_matches_shared_area_audit() -> None:
    rows = {str(row["name"]): row for row in load_monster_rows()}
    for template_id, source_name in {
        "srd-black-dragon-wyrmling": "Black Dragon Wyrmling",
        "srd-blue-dragon-wyrmling": "Blue Dragon Wyrmling",
        "srd-young-black-dragon": "Young Black Dragon",
        "srd-young-blue-dragon": "Young Blue Dragon",
    }.items():
        monster = build_combatant_from_capabilities(template_id)
        action = monster.saving_throw_actions[0]
        assert save_math_issues(action, str(rows[source_name]["actions"])) == []


def test_recharge_breath_family_uses_shared_resource_and_area_primitives() -> None:
    expected = {
        "srd-green-dragon-wyrmling": ("cone", 15, None, "constitution", 11, 6, 6, "poison"),
        "srd-black-dragon-wyrmling": ("line", 15, 5, "dexterity", 11, 5, 8, "acid"),
        "srd-blue-dragon-wyrmling": ("line", 30, 5, "dexterity", 12, 6, 6, "lightning"),
        "srd-red-dragon-wyrmling": ("cone", 15, None, "dexterity", 13, 7, 6, "fire"),
        "srd-white-dragon-wyrmling": ("cone", 15, None, "constitution", 12, 5, 8, "cold"),
        "srd-hell-hound": ("cone", 15, None, "dexterity", 12, 5, 6, "fire"),
        "srd-young-black-dragon": ("line", 30, 5, "dexterity", 14, 14, 6, "acid"),
        "srd-young-blue-dragon": ("line", 60, 5, "dexterity", 16, 10, 10, "lightning"),
        "srd-young-green-dragon": ("cone", 30, None, "constitution", 14, 12, 6, "poison"),
        "srd-young-red-dragon": ("cone", 30, None, "dexterity", 17, 16, 6, "fire"),
        "srd-young-white-dragon": ("cone", 30, None, "constitution", 15, 9, 8, "cold"),
    }
    for template_id, values in expected.items():
        monster = build_combatant_from_capabilities(template_id)
        action = monster.saving_throw_actions[0]
        resource = monster.resources[0]
        shape, size_ft, width_ft, ability, dc, count, die, damage_type = values
        assert (action.area.shape, action.area.size_ft, action.area.width_ft) == (shape, size_ft, width_ft)
        assert (action.save_ability, action.dc) == (ability, dc)
        assert (action.damage_dice_count, action.damage_dice_size, action.damage_type) == (count, die, damage_type)
        assert action.success_damage == "half"
        assert action.resource_id == resource.id
        assert (resource.max_uses, resource.recharge.minimum, resource.recharge.maximum) == (1, 5, 6)


def test_young_chromatic_dragons_use_three_rend_slots() -> None:
    for template_id in (
        "srd-young-black-dragon", "srd-young-blue-dragon", "srd-young-green-dragon",
        "srd-young-red-dragon", "srd-young-white-dragon",
    ):
        dragon = build_combatant_from_capabilities(template_id)
        assert dragon.attack_action is not None
        assert len(dragon.attack_action.slots) == 3
        assert all(slot.attack_ids == [dragon.weapon_attack.id] for slot in dragon.attack_action.slots)


def test_hell_hound_uses_existing_pack_tactics_trait() -> None:
    hound = build_combatant_from_capabilities("srd-hell-hound")
    assert hound.combat_traits == [CombatTrait.PACK_TACTICS]
    assert hound.source_trait_names == ["Pack Tactics"]


def test_swarm_of_insects_uses_existing_swarm_and_bloodied_capabilities() -> None:
    swarm = build_combatant_from_capabilities("srd-swarm-of-insects")
    attack = swarm.weapon_attack
    assert swarm.combat_traits == [CombatTrait.SWARM]
    assert swarm.speed_ft == 20
    assert swarm.movement_modes.fly_ft == 20
    assert swarm.source_trait_names == ["Spider Climb", "Swarm"]
    assert (attack.weapon.dice_count, attack.weapon.dice_size, attack.damage_bonus) == (2, 4, 1)
    assert len(attack.conditional_damage) == 1
    bloodied = attack.conditional_damage[0]
    assert (bloodied.trigger, bloodied.mode) == ("attacker_bloodied", "replace_weapon")
    assert (bloodied.dice_count, bloodied.dice_size, bloodied.damage_bonus) == (1, 4, 1)


def test_swarm_of_venomous_snakes_preserves_poison_when_bloodied() -> None:
    swarm = build_combatant_from_capabilities("srd-swarm-of-venomous-snakes")
    attack = swarm.weapon_attack
    assert swarm.combat_traits == [CombatTrait.SWARM]
    assert swarm.movement_modes.swim_ft == 30
    assert (attack.weapon.dice_count, attack.weapon.dice_size, attack.damage_bonus) == (1, 8, 4)
    assert len(attack.on_hit_damage) == 1
    poison = attack.on_hit_damage[0]
    assert (poison.dice_count, poison.dice_size, poison.damage_bonus, poison.damage_type.value) == (3, 6, 0, "poison")
    assert len(attack.conditional_damage) == 1
    bloodied = attack.conditional_damage[0]
    assert (bloodied.trigger, bloodied.mode) == ("attacker_bloodied", "replace_weapon")
    assert (bloodied.dice_count, bloodied.dice_size, bloodied.damage_bonus) == (1, 4, 4)
