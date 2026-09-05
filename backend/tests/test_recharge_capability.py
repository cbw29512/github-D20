from __future__ import annotations

from app.content.capability_compiler import compile_combatant
from app.content.capability_from_template import definition_from_template
from app.domain.capabilities import CombatantDefinition


def _definition() -> CombatantDefinition:
    return CombatantDefinition.model_validate({
        "id": "recharge-contract",
        "name": "Recharge Contract",
        "archetype": "contract",
        "kind": "monster",
        "armor_class": 12,
        "max_hp": 20,
        "speed_ft": 30,
        "initiative_bonus": 1,
        "attacks": [{
            "id": "bite",
            "name": "Bite",
            "attack_kind": "melee",
            "attack_bonus": 4,
            "damage": {"count": 1, "size": 6, "bonus": 2},
            "damage_type": "piercing",
            "animation": "bite",
        }],
        "primary_attack_id": "bite",
        "resources": [{
            "id": "fire-breath",
            "name": "Fire Breath",
            "max_uses": 1,
            "recharge": {"minimum": 5, "maximum": 6},
        }],
        "visual": {"armor": "natural", "main_hand": "bite", "body_style": "beast"},
        "source": "recharge-contract-test",
    })


def test_recharge_metadata_survives_capability_compile_and_round_trip() -> None:
    template = compile_combatant(_definition())
    assert template.resources[0].recharge is not None
    assert template.resources[0].recharge.minimum == 5
    round_trip = definition_from_template(template)
    assert round_trip.resources[0].recharge is not None
    assert round_trip.resources[0].recharge.maximum == 6
