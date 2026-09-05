from app.content.mechanic_family_inventory import (
    build_hero_mechanic_demand,
    build_monster_mechanic_families,
)


def _families() -> dict[str, set[str]]:
    return {
        family.id: set(family.monster_names)
        for family in build_monster_mechanic_families()
    }


def test_mechanic_family_inventory_groups_repeated_monster_math() -> None:
    families = _families()
    assert "Wolf" in families["pack-tactics"]
    assert "Hell Hound" in families["recharge"]
    assert "Stirge" in families["attachment"]
    assert "Stirge" in families["recurring-turn-damage"]


def test_injured_target_advantage_is_one_cross_source_family() -> None:
    assert _families()["injured-target-advantage"] == {
        "Giant Shark",
        "Hunter Shark",
        "Piranha",
        "Sahuagin Warrior",
        "Swarm of Piranhas",
    }


def test_hit_point_maximum_reduction_is_one_shared_survival_family() -> None:
    assert _families()["hit-point-maximum-reduction"] == {
        "Clay Golem",
        "Death Dog",
        "Mummy",
        "Mummy Lord",
        "Night Hag",
        "Otyugh",
        "Specter",
        "Succubus",
        "Vampire",
        "Vampire Spawn",
        "Wight",
        "Wraith",
    }


def test_mechanic_family_inventory_exposes_cross_class_hero_demand() -> None:
    demand = build_hero_mechanic_demand()
    owners = {owner for class_owners in demand.values() for owner in class_owners}
    assert owners == {
        "barbarian", "bard", "cleric", "druid", "fighter", "monk",
        "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    }
    assert demand
