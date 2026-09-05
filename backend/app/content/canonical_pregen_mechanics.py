from __future__ import annotations

from dataclasses import dataclass

from app.content.character_combat_recipe import compose_character_combat_recipe
from app.content.combat_build_variants import get_combat_build_variant
from app.content.hero_progressions import CANONICAL_HEROES
from app.content.subclass_specializations import subclass_specialization


CANONICAL_BUILD_BY_CLASS = {
    "barbarian": "great-weapon",
    "bard": "support-healer",
    "cleric": "healer",
    "druid": "land-damage",
    "fighter": "great-weapon",
    "monk": "unarmed-offense",
    "paladin": "sword-shield",
    "ranger": "sword-shield",
    "rogue": "dual-wield",
    "sorcerer": "fire-damage",
    "warlock": "blaster",
    "wizard": "fire-damage",
}


@dataclass(frozen=True)
class PregenMechanicRequirement:
    id: str
    kinds: tuple[str, ...]
    owners: tuple[str, ...]

    @property
    def demand_count(self) -> int:
        return len(self.owners)


def derive_canonical_pregen_mechanics() -> tuple[PregenMechanicRequirement, ...]:
    """Return the exact combat-only mechanic inventory for all 12 pregens, levels 1-20."""
    items: dict[str, dict[str, set[str]]] = {}

    def add(mechanic_id: str, kind: str, owner: str) -> None:
        item = items.setdefault(mechanic_id, {"kinds": set(), "owners": set()})
        item["kinds"].add(kind)
        item["owners"].add(owner)

    for hero in CANONICAL_HEROES:
        build_id = CANONICAL_BUILD_BY_CLASS[hero.class_id]
        variant = get_combat_build_variant(hero.class_id, build_id)
        if variant.required_subclass_id != hero.subclass_id:
            raise ValueError(
                f"Canonical {hero.class_id} build {build_id} targets "
                f"{variant.required_subclass_id}, not {hero.subclass_id}."
            )

        for level in range(1, 21):
            recipe = compose_character_combat_recipe(
                hero.class_id,
                hero.subclass_id,
                build_id,
                level,
            )
            for feature_id in recipe.combat_features:
                add(feature_id, "combat-feature", hero.class_id)

        recipe = compose_character_combat_recipe(
            hero.class_id,
            hero.subclass_id,
            build_id,
            20,
        )
        if recipe.build_choices is not None:
            for capability_id in recipe.build_choices.required_capabilities:
                add(capability_id, "loadout-capability", hero.class_id)

        specialization = subclass_specialization(hero.subclass_id)
        if specialization.spell_package_id:
            add(
                f"spell-package:{specialization.spell_package_id}",
                "spell-package",
                hero.class_id,
            )
        for choice_id in specialization.feature_choice_ids:
            add(f"feature-choice:{choice_id}", "feature-choice", hero.class_id)

    requirements = (
        PregenMechanicRequirement(
            id=mechanic_id,
            kinds=tuple(sorted(item["kinds"])),
            owners=tuple(sorted(item["owners"])),
        )
        for mechanic_id, item in items.items()
    )
    return tuple(sorted(requirements, key=lambda item: (-item.demand_count, item.id)))
