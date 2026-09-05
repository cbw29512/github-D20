from __future__ import annotations

from dataclasses import dataclass

from app.content.canonical_pregen_mechanics import derive_canonical_pregen_mechanics


SPELLCASTING_CLASSES = frozenset({
    "bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock", "wizard",
})


@dataclass(frozen=True)
class PregenEngineGroup:
    id: str
    owners: tuple[str, ...]
    mechanics: tuple[str, ...]

    @property
    def demand_count(self) -> int:
        return len(self.owners)


def engine_group_for(mechanic_id: str, kinds: tuple[str, ...]) -> str:
    """Map class-facing feature ids onto reusable combat-engine primitives."""
    if "spell-package" in kinds:
        return "spellcasting"
    if mechanic_id.endswith("-spellcasting") or "-combat-spells-" in mechanic_id:
        return "spellcasting"
    return mechanic_id


def derive_canonical_pregen_engine_groups() -> tuple[PregenEngineGroup, ...]:
    grouped: dict[str, dict[str, set[str]]] = {}
    for requirement in derive_canonical_pregen_mechanics():
        group_id = engine_group_for(requirement.id, requirement.kinds)
        item = grouped.setdefault(group_id, {"owners": set(), "mechanics": set()})
        item["owners"].update(requirement.owners)
        item["mechanics"].add(requirement.id)

    groups = (
        PregenEngineGroup(
            id=group_id,
            owners=tuple(sorted(item["owners"])),
            mechanics=tuple(sorted(item["mechanics"])),
        )
        for group_id, item in grouped.items()
    )
    return tuple(sorted(groups, key=lambda item: (-item.demand_count, item.id)))
