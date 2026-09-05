from __future__ import annotations

from app.content.figure_profiles import FigureProfile, MONSTER_FIGURE_PROFILES

_NATIVE_FIGURE_PROFILES: dict[str, FigureProfile] = {
    "Ape": {"form": "primate", "detail": "ape"},
    "Black Dragon Wyrmling": {"form": "reptile", "detail": "black-dragon-wyrmling"},
    "Blue Dragon Wyrmling": {"form": "reptile", "detail": "blue-dragon-wyrmling"},
    "Green Dragon Wyrmling": {"form": "reptile", "detail": "green-dragon-wyrmling"},
    "Hell Hound": {"form": "quadruped", "detail": "hell-hound"},
    "Red Dragon Wyrmling": {"form": "reptile", "detail": "red-dragon-wyrmling"},
    "White Dragon Wyrmling": {"form": "reptile", "detail": "white-dragon-wyrmling"},
    "Winter Wolf": {"form": "quadruped", "detail": "winter-wolf"},
    "Young Black Dragon": {"form": "reptile", "detail": "young-black-dragon"},
    "Young Blue Dragon": {"form": "reptile", "detail": "young-blue-dragon"},
    "Young Green Dragon": {"form": "reptile", "detail": "young-green-dragon"},
    "Young Red Dragon": {"form": "reptile", "detail": "young-red-dragon"},
    "Young White Dragon": {"form": "reptile", "detail": "young-white-dragon"},
}


def reviewed_monster_figure_profiles() -> dict[str, FigureProfile]:
    overlap = set(MONSTER_FIGURE_PROFILES) & set(_NATIVE_FIGURE_PROFILES)
    if overlap:
        raise ValueError(f"Figure profile names overlap across registries: {sorted(overlap)}")
    return {**MONSTER_FIGURE_PROFILES, **_NATIVE_FIGURE_PROFILES}
