from app.content.canonical_pregen_engine_groups import SPELLCASTING_CLASSES
from app.content.canonical_pregen_spell_gaps import (
    canonical_pregen_spell_package_gaps,
    first_spell_package_gap_by_class,
)


def test_spell_gap_scan_is_limited_to_the_eight_canonical_casters() -> None:
    gaps = canonical_pregen_spell_package_gaps()
    assert {gap.class_id for gap in gaps} <= SPELLCASTING_CLASSES


def test_first_gap_report_has_one_entry_for_every_canonical_caster() -> None:
    report = first_spell_package_gap_by_class()
    assert set(report) == SPELLCASTING_CLASSES
    for class_id, gap in report.items():
        if gap is not None:
            assert gap.class_id == class_id
            assert 1 <= gap.level <= 20
            assert gap.reason
