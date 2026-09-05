from __future__ import annotations

from functools import lru_cache
import re

from app.domain.models import CombatantTemplate
from app.domain.movement import MovementModes

_BASE_WALK = re.compile(r"^\s*(\d+)\s*ft\b", re.IGNORECASE)
_FLY = re.compile(r"\bfly\s+(\d+)\s*ft\b", re.IGNORECASE)
_SWIM = re.compile(r"\bswim\s+(\d+)\s*ft\b", re.IGNORECASE)


@lru_cache(maxsize=1)
def _source_speed_by_name() -> dict[str, object]:
    # Local import avoids a module-load cycle while keeping the catalog's
    # existing name-based eligibility call source-derived.
    from app.content.monster_catalog import load_monster_rows

    return {str(row["name"]): row["speed"] for row in load_monster_rows()}


def _source_environment_speeds(source_speed: object) -> tuple[int, int, int]:
    """Read only walk/fly/swim facts needed for standard-arena eligibility."""
    text = str(source_speed or "").strip()
    if not (_BASE_WALK.search(text) or _FLY.search(text) or _SWIM.search(text)):
        text = str(_source_speed_by_name().get(text, text)).strip()
    walk = _BASE_WALK.search(text)
    fly = _FLY.search(text)
    swim = _SWIM.search(text)
    return (
        int(walk.group(1)) if walk else 0,
        int(fly.group(1)) if fly else 0,
        int(swim.group(1)) if swim else 0,
    )


def deferred_environment_reason(source: object | MovementModes) -> str | None:
    """Return environment blockers without invoking the stricter runtime movement parser."""
    if isinstance(source, MovementModes):
        walk_ft, fly_ft, swim_ft = source.walk_ft, source.fly_ft, source.swim_ft
    else:
        walk_ft, fly_ft, swim_ft = _source_environment_speeds(source)
    if fly_ft > 0:
        return None
    if swim_ft > 0 and walk_ft <= 5:
        return "aquatic-only"
    return None


def standard_arena_eligible(template: CombatantTemplate) -> bool:
    """Ignore movement-only rules; reject creatures that cannot function in the standard arena."""
    if template.kind != "monster":
        return True
    movement = template.movement_modes
    if deferred_environment_reason(movement) is not None:
        return False
    return any((
        movement.walk_ft > 0,
        movement.fly_ft > 0,
        movement.climb_ft > 0,
        movement.swim_ft > 0,
        movement.burrow_ft > 0,
    ))


def filter_standard_arena_eligible(templates: list[CombatantTemplate]) -> list[CombatantTemplate]:
    return [template for template in templates if standard_arena_eligible(template)]
