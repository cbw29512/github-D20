from __future__ import annotations

import logging

from app.content.capability_registry import build_monster_templates_from_capabilities
from app.content.certified_heroes import build_certified_hero_templates
from app.content.unarmed_opportunity_profiles import complete_unarmed_opportunity_profiles
from app.domain.models import ArenaRoster

logger = logging.getLogger(__name__)


def build_arena_roster() -> ArenaRoster:
    try:
        characters = complete_unarmed_opportunity_profiles(build_certified_hero_templates())
        monsters = complete_unarmed_opportunity_profiles(build_monster_templates_from_capabilities())
        return ArenaRoster(characters=characters, monsters=monsters)
    except Exception as exc:
        logger.exception("Failed to build Iron Pit arena roster.")
        raise RuntimeError("Arena roster could not be created.") from exc
