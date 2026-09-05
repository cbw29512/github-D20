from app.content.canonical_pregen_engine_groups import (
    SPELLCASTING_CLASSES,
    derive_canonical_pregen_engine_groups,
    engine_group_for,
)


def test_class_spellcasting_features_share_one_engine_group() -> None:
    assert engine_group_for("bard-spellcasting", ("combat-feature",)) == "spellcasting"
    assert engine_group_for("wizard-combat-spells-5", ("combat-feature",)) == "spellcasting"
    assert engine_group_for("spell-package:college-lore", ("spell-package",)) == "spellcasting"


def test_spellcasting_is_the_shared_primitive_for_all_canonical_casters() -> None:
    groups = {group.id: group for group in derive_canonical_pregen_engine_groups()}
    spellcasting = groups["spellcasting"]
    assert set(spellcasting.owners) == SPELLCASTING_CLASSES
    assert spellcasting.demand_count == 8


def test_engine_groups_remain_ranked_by_pregen_reuse() -> None:
    groups = derive_canonical_pregen_engine_groups()
    counts = [group.demand_count for group in groups]
    assert counts == sorted(counts, reverse=True)
