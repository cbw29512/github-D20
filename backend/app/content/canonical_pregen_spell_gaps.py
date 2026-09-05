from __future__ import annotations

from dataclasses import dataclass

from app.content.canonical_pregen_engine_groups import SPELLCASTING_CLASSES
from app.content.canonical_spell_packages import build_class_spell_package


@dataclass(frozen=True)
class SpellPackageGap:
    class_id: str
    level: int
    reason: str


def canonical_pregen_spell_package_gaps() -> tuple[SpellPackageGap, ...]:
    """Report every canonical caster level whose combat spell package is incomplete."""
    gaps: list[SpellPackageGap] = []
    for class_id in sorted(SPELLCASTING_CLASSES):
        for level in range(1, 21):
            try:
                build_class_spell_package(class_id, level)  # type: ignore[arg-type]
            except (KeyError, ValueError) as exc:
                gaps.append(SpellPackageGap(class_id, level, str(exc)))
    return tuple(gaps)


def first_spell_package_gap_by_class() -> dict[str, SpellPackageGap | None]:
    first: dict[str, SpellPackageGap | None] = {class_id: None for class_id in SPELLCASTING_CLASSES}
    for gap in canonical_pregen_spell_package_gaps():
        if first[gap.class_id] is None:
            first[gap.class_id] = gap
    return dict(sorted(first.items()))
