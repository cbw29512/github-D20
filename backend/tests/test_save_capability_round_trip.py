from app.content.capability_compiler import compile_combatant
from app.content.capability_from_template import definition_from_template
from app.content.monster_goat import build_goat
from app.domain.actions import SavingThrowAction
from app.domain.areas import AreaGeometry
from app.domain.combatants import RechargeDefinition, ResourceDefinition


def test_save_resource_and_area_survive_capability_round_trip() -> None:
    source = build_goat().model_copy(update={
        "resources": [
            ResourceDefinition(
                id="test-breath", name="Test Breath", max_uses=1,
                recharge=RechargeDefinition(minimum=5, maximum=6, die_size=6),
            ),
        ],
        "saving_throw_actions": [
            SavingThrowAction(
                id="test-breath", name="Test Breath", save_ability="constitution", dc=11,
                range_ft=15, area=AreaGeometry(shape="cone", size_ft=15),
                damage_dice_count=6, damage_dice_size=6, damage_type="poison",
                success_damage="half", resource_id="test-breath", resource_cost=1,
            ),
        ],
    })

    definition = definition_from_template(source)
    declared = definition.save_actions[0]
    assert declared.resource_id == "test-breath"
    assert declared.resource_cost == 1
    assert declared.area == AreaGeometry(shape="cone", size_ft=15)

    compiled = compile_combatant(definition)
    action = compiled.saving_throw_actions[0]
    assert action.resource_id == "test-breath"
    assert action.resource_cost == 1
    assert action.area == AreaGeometry(shape="cone", size_ft=15)
    assert compiled.resources[0].recharge == RechargeDefinition(minimum=5, maximum=6, die_size=6)
