from app.content.monster_catalog import build_monster_catalog
from app.domain.catalog import CoverageStatus


YOUNG_CHROMATIC_IDS = {
    "Young Black Dragon": "srd-young-black-dragon",
    "Young Blue Dragon": "srd-young-blue-dragon",
    "Young Green Dragon": "srd-young-green-dragon",
    "Young Red Dragon": "srd-young-red-dragon",
    "Young White Dragon": "srd-young-white-dragon",
}


def test_young_chromatic_dragons_are_public_ready() -> None:
    cards = {card.name: card for card in build_monster_catalog()}
    for name, runtime_id in YOUNG_CHROMATIC_IDS.items():
        card = cards[name]
        assert card.coverage_status is CoverageStatus.RAW_READY
        assert card.runnable_template_id == runtime_id
        assert card.blockers == []
