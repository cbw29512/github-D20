from app.content.capability_registry import build_combatant_from_capabilities, get_capability_definition
from app.content.monster_catalog import build_monster_catalog, load_monster_rows
from app.content.monster_limited_use_source_audit import source_limited_use_names
from app.content.monster_source_audit import audit_monster_source
from app.domain.catalog import CoverageStatus


def _source_row(name: str) -> dict[str, object]:
    return next(row for row in load_monster_rows() if row["name"] == name)


def test_green_dragon_wyrmling_native_capabilities_match_srd_source() -> None:
    definition = get_capability_definition("srd-green-dragon-wyrmling")
    assert definition.source_limited_use_names == source_limited_use_names("Green Dragon Wyrmling")

    template = build_combatant_from_capabilities("srd-green-dragon-wyrmling")
    assert audit_monster_source(template, _source_row("Green Dragon Wyrmling")) == []
    assert template.damage_immunities == ["poison"]
    assert template.condition_immunities == ["poisoned"]

    assert template.attack_action is not None
    assert len(template.attack_action.slots) == 2
    assert all(slot.attack_ids == ["srd-green-dragon-wyrmling-rend"] for slot in template.attack_action.slots)
    assert template.weapon_attack.weapon.dice_count == 1
    assert template.weapon_attack.weapon.dice_size == 10
    assert template.weapon_attack.damage_bonus == 2
    assert [(item.dice_count, item.dice_size, item.damage_type.value) for item in template.weapon_attack.on_hit_damage] == [(1, 6, "poison")]

    breath = template.saving_throw_actions[0]
    assert (breath.name, breath.save_ability, breath.dc) == ("Poison Breath", "constitution", 11)
    assert (breath.damage_dice_count, breath.damage_dice_size, breath.damage_type, breath.success_damage) == (6, 6, "poison", "half")
    assert breath.area is not None and (breath.area.shape, breath.area.size_ft) == ("cone", 15)
    resource = template.resources[0]
    assert resource.id == breath.resource_id and resource.max_uses == 1
    assert resource.recharge is not None and (resource.recharge.minimum, resource.recharge.maximum) == (5, 6)


def test_green_dragon_wyrmling_is_raw_ready_only_after_full_source_audit() -> None:
    card = next(card for card in build_monster_catalog() if card.name == "Green Dragon Wyrmling")
    assert card.coverage_status == CoverageStatus.RAW_READY
    assert card.runnable_template_id == "srd-green-dragon-wyrmling"
    assert card.blockers == []
