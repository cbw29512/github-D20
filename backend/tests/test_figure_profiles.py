from app.content.figure_profile_registry import reviewed_monster_figure_profiles
from app.content.monster_catalog import build_monster_catalog
from app.domain.catalog import CoverageStatus


def _profiles():
    return reviewed_monster_figure_profiles()


def test_every_raw_ready_monster_has_a_reviewed_figure_profile() -> None:
    ready_names = {
        card.name
        for card in build_monster_catalog()
        if card.coverage_status is CoverageStatus.RAW_READY
    }
    assert ready_names <= set(_profiles())


def test_reviewed_profiles_are_explicit_and_nonempty() -> None:
    for name, profile in _profiles().items():
        assert profile["form"]
        assert profile["detail"]
        assert profile["form"] != "unknown", f"{name} cannot be certified with an unknown silhouette"


def test_anatomically_distinct_monsters_do_not_share_humanoid_fallbacks() -> None:
    expected = {
        "Animated Flying Sword": "weapon", "Ankylosaurus": "reptile", "Archelon": "aquatic-reptile",
        "Axe Beak": "bird", "Baboon": "primate", "Blood Hawk": "bird", "Flying Snake": "snake",
        "Gargoyle": "gargoyle", "Giant Constrictor Snake": "snake", "Giant Crocodile": "reptile",
        "Giant Eagle": "bird", "Giant Elk": "hoofed", "Giant Wolf Spider": "spider", "Goat": "hoofed",
        "Green Dragon Wyrmling": "reptile", "Hippogriff": "hippogriff", "Hippopotamus": "quadruped",
        "Killer Whale": "aquatic-mammal", "Lemure": "brute", "Manticore": "quadruped",
        "Minotaur Skeleton": "brute", "Owlbear": "bear", "Pegasus": "hoofed",
        "Plesiosaurus": "aquatic-reptile", "Pteranodon": "pterosaur", "Reef Shark": "aquatic-fish",
        "Rhinoceros": "hoofed", "Scorpion": "scorpion", "Spider": "spider", "Swarm of Bats": "swarm",
        "Swarm of Crawling Claws": "swarm", "Swarm of Insects": "swarm", "Swarm of Rats": "swarm",
        "Swarm of Venomous Snakes": "swarm", "Triceratops": "reptile",
        "Tyrannosaurus Rex": "theropod", "Worg": "quadruped",
    }
    profiles = _profiles()
    for name, form in expected.items():
        assert profiles[name]["form"] == form


def test_new_batch_has_specific_reviewed_details() -> None:
    expected = {
        "Animated Armor": "animated-armor", "Animated Flying Sword": "flying-sword", "Awakened Tree": "tree",
        "Blood Hawk": "blood-hawk", "Flying Snake": "flying-snake", "Gargoyle": "gargoyle", "Goat": "goat",
        "Goblin Boss": "goblin-boss", "Green Dragon Wyrmling": "green-dragon-wyrmling",
        "Grimlock": "grimlock", "Guard Captain": "guard-captain", "Hippopotamus": "hippopotamus",
        "Killer Whale": "orca", "Lemure": "lemure", "Manticore": "manticore",
        "Merfolk Skirmisher": "merfolk-skirmisher", "Minotaur Skeleton": "minotaur-skeleton",
        "Pegasus": "pegasus", "Reef Shark": "shark", "Scorpion": "scorpion", "Skeleton": "skeleton",
        "Swarm of Bats": "bats", "Swarm of Crawling Claws": "crawling-claws", "Swarm of Insects": "insects",
        "Swarm of Rats": "rats", "Swarm of Venomous Snakes": "venomous-snakes", "Triceratops": "triceratops",
        "Violet Fungus": "violet-fungus", "Worg": "canine",
    }
    profiles = _profiles()
    for name, detail in expected.items():
        assert profiles[name]["detail"] == detail
