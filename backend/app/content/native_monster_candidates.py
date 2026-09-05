from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def native_monster_candidates() -> dict[str, str]:
    from app.content.capability_registry import load_capability_definitions

    definitions = load_capability_definitions().values()
    candidates = {
        definition.name: definition.id
        for definition in definitions
        if definition.kind == "monster" and definition.source.startswith("SRD 5.2.1 p. ")
    }
    source_ids = {
        definition.id
        for definition in definitions
        if definition.kind == "monster" and definition.source.startswith("SRD 5.2.1 p. ")
    }
    if len(candidates) != len(source_ids):
        raise ValueError("Native SRD monster candidate names must be unique.")
    return candidates


def candidate_id(name: str, legacy: dict[str, str]) -> str | None:
    return legacy.get(name) or native_monster_candidates().get(name)
