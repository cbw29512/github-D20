from __future__ import annotations

import logging

from app.domain.models import CombatantState, ResourceState

logger = logging.getLogger(__name__)


def get_resource(state: CombatantState, resource_id: str) -> ResourceState | None:
    """Return one runtime resource by stable ID."""
    return next((item for item in state.resources if item.id == resource_id), None)


def resource_uses(state: CombatantState, resource_id: str) -> int:
    item = get_resource(state, resource_id)
    return item.current_uses if item is not None else 0


def spend_resource(state: CombatantState, resource_id: str, amount: int = 1) -> ResourceState:
    """Spend a shared runtime resource and fail closed when unavailable."""
    try:
        if amount <= 0:
            raise ValueError("Resource spend must be positive.")
        item = get_resource(state, resource_id)
        if item is None:
            raise ValueError(f"Resource {resource_id!r} is missing.")
        if item.current_uses < amount:
            raise ValueError(f"Resource {resource_id!r} has insufficient uses.")
        item.current_uses -= amount
        return item
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Failed to spend resource %s for %s.", resource_id, state.template.name)
        raise RuntimeError("Combat resource could not be spent.") from exc


def restore_resource(state: CombatantState, resource_id: str, amount: int | None = None) -> ResourceState:
    """Restore a resource without exceeding its runtime maximum."""
    try:
        item = get_resource(state, resource_id)
        if item is None:
            raise ValueError(f"Resource {resource_id!r} is missing.")
        if amount is not None and amount <= 0:
            raise ValueError("Resource restore must be positive.")
        item.current_uses = item.max_uses if amount is None else min(item.max_uses, item.current_uses + amount)
        return item
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Failed to restore resource %s for %s.", resource_id, state.template.name)
        raise RuntimeError("Combat resource could not be restored.") from exc
