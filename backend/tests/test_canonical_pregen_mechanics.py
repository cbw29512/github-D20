from app.content.canonical_pregen_mechanics import (
    CANONICAL_BUILD_BY_CLASS,
    derive_canonical_pregen_mechanics,
)
from app.content.combat_build_variants import get_combat_build_variant
from app.content.hero_progressions import CANONICAL_HEROES


def test_every_canonical_hero_has_one_exact_combat_build() -> None:
    assert set(CANONICAL_BUILD_BY_CLASS) == {hero.class_id for hero in CANONICAL_HEROES}
    for hero in CANONICAL_HEROES:
        variant = get_combat_build_variant(hero.class_id, CANONICAL_BUILD_BY_CLASS[hero.class_id])
        assert variant.required_subclass_id == hero.subclass_id


def test_canonical_pregen_inventory_is_combat_only_and_ranked_by_reuse() -> None:
    requirements = derive_canonical_pregen_mechanics()
    assert requirements
    assert all("arena-ignored" not in item.kinds for item in requirements)
    assert [item.demand_count for item in requirements] == sorted(
        (item.demand_count for item in requirements), reverse=True
    )


def test_inventory_covers_all_twelve_pregens() -> None:
    requirements = derive_canonical_pregen_mechanics()
    owners = {owner for item in requirements for owner in item.owners}
    assert owners == {hero.class_id for hero in CANONICAL_HEROES}


def test_shared_mechanics_are_detectable_before_class_specific_work() -> None:
    shared = {item.id: item.owners for item in derive_canonical_pregen_mechanics() if item.demand_count > 1}
    assert "extra-attack" in shared
    assert {"barbarian", "fighter"} <= set(shared["extra-attack"])
