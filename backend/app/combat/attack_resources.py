from __future__ import annotations

import logging

from app.combat.resource_pool import resource_uses, spend_resource
from app.domain.models import CombatantState, WeaponAttack

logger = logging.getLogger(__name__)


def attack_resource_available(state: CombatantState, attack: WeaponAttack) -> bool:
    if attack.resource_id is None:
        return True
    return resource_uses(state, attack.resource_id) >= attack.resource_cost


def spend_attack_resource(state: CombatantState, attack: WeaponAttack) -> int | None:
    """Spend one attack-owned resource; return remaining uses for event/reporting callers."""
    if attack.resource_id is None:
        return None
    try:
        resource = spend_resource(state, attack.resource_id, attack.resource_cost)
        return resource.current_uses
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Failed to spend attack resource for %s using %s.", state.template.name, attack.id)
        raise RuntimeError("Attack resource could not be spent.") from exc
