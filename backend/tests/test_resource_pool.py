from __future__ import annotations

import pytest

from app.combat.resource_pool import get_resource, resource_uses, restore_resource, spend_resource
from app.combat.state import build_combatant_state
from app.content.audited_fighter import build_karnok_stoneward


def _state():
    return build_combatant_state(build_karnok_stoneward())


def test_shared_resource_pool_spends_by_stable_id() -> None:
    state = _state()
    before = resource_uses(state, "second-wind")
    item = spend_resource(state, "second-wind")
    assert item.current_uses == before - 1
    assert get_resource(state, "second-wind") is item


def test_shared_resource_pool_fails_closed_for_missing_or_exhausted_resource() -> None:
    state = _state()
    with pytest.raises(ValueError, match="missing"):
        spend_resource(state, "not-a-resource")
    item = get_resource(state, "second-wind")
    assert item is not None
    item.current_uses = 0
    with pytest.raises(ValueError, match="insufficient"):
        spend_resource(state, "second-wind")


def test_shared_resource_pool_restore_caps_at_maximum() -> None:
    state = _state()
    item = get_resource(state, "second-wind")
    assert item is not None
    item.current_uses = 0
    restored = restore_resource(state, "second-wind", 999)
    assert restored.current_uses == restored.max_uses
