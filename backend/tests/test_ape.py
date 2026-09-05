from app.combat.attack_resources import attack_resource_available, spend_attack_resource
from app.combat.dice import FixedDiceProvider
from app.combat.pit_policy import choose_resource_backed_attack
from app.combat.recharge import resolve_recharge_start_of_turn
from app.combat.state import build_combatant_state
from app.content.audited_fighter import build_karnok_stoneward
from app.content.capability_registry import build_combatant_from_capabilities, get_capability_definition
from app.content.monster_catalog import build_monster_catalog, load_monster_rows
from app.content.monster_source_audit import audit_monster_source
from app.domain.catalog import CoverageStatus
from app.domain.encounters import EncounterCombatant, EncounterSetup


def _source_row(name: str) -> dict[str, object]:
    return next(row for row in load_monster_rows() if row["name"] == name)


def _setup() -> tuple[EncounterCombatant, EncounterCombatant, EncounterSetup]:
    ape = EncounterCombatant(
        combatant_id="monster-1:srd-ape", side="monsters", position_ft=10,
        state=build_combatant_state(build_combatant_from_capabilities("srd-ape")),
    )
    hero = EncounterCombatant(
        combatant_id="hero-1:karnok", side="heroes", position_ft=5,
        state=build_combatant_state(build_karnok_stoneward()),
    )
    return ape, hero, EncounterSetup(
        heroes=[hero], monsters=[ape], hero_total_levels=1, monster_total_cr="1/2", starting_distance_ft=5,
    )


def test_ape_native_capabilities_match_srd_source() -> None:
    definition = get_capability_definition("srd-ape")
    template = build_combatant_from_capabilities("srd-ape")
    assert definition.source_limited_use_names == ["actions:Rock (Recharge 6)"]
    assert audit_monster_source(template, _source_row("Ape")) == []
    assert template.attack_action is not None
    assert [slot.attack_ids for slot in template.attack_action.slots] == [["srd-ape-fist"], ["srd-ape-fist"]]
    rock = next(attack for attack in template.alternate_weapon_attacks if attack.id == "srd-ape-rock")
    assert (rock.attack_bonus, rock.weapon.dice_count, rock.weapon.dice_size, rock.damage_bonus) == (5, 2, 6, 3)
    assert (rock.weapon.normal_range_ft, rock.weapon.long_range_ft) == (25, 50)
    assert (rock.resource_id, rock.resource_cost) == ("srd-ape-rock-recharge", 1)
    resource = template.resources[0]
    assert resource.recharge is not None
    assert (resource.max_uses, resource.recharge.minimum, resource.recharge.maximum) == (1, 6, 6)


def test_ape_rock_depletes_then_recharges_through_shared_attack_resource() -> None:
    ape, _hero, setup = _setup()
    choice = choose_resource_backed_attack(ape, setup)
    assert choice is not None and choice[1].id == "srd-ape-rock"
    rock = choice[1]
    assert attack_resource_available(ape.state, rock)
    assert spend_attack_resource(ape.state, rock) == 0
    assert not attack_resource_available(ape.state, rock)
    assert choose_resource_backed_attack(ape, setup) is None

    resource = ape.state.template.resources[0]
    assert resource.recharge is not None
    result = resolve_recharge_start_of_turn(ape.state, resource.id, resource.recharge, FixedDiceProvider([6]))
    assert result.recharged and result.resource_remaining == 1
    assert choose_resource_backed_attack(ape, setup) is not None


def test_ape_is_raw_ready_after_shared_recharge_attack_certification() -> None:
    card = next(card for card in build_monster_catalog() if card.name == "Ape")
    assert card.coverage_status == CoverageStatus.RAW_READY
    assert card.runnable_template_id == "srd-ape"
    assert card.blockers == []
