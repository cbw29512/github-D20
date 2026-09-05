from app.content.monster_bonus_action_source_audit import arena_neutral_bonus_action_source
from app.content.monster_combat_scope import combat_math_relevant, feature_blocks
from app.content.monster_legendary_source_audit import legendary_source_relevant
from app.content.monster_limited_use_source_audit import limited_use_source_relevant, parse_limited_use_names
from app.content.monster_reaction_source_audit import arena_neutral_reaction_source
from app.content.monster_trait_source_audit import combat_relevant_trait_names


def test_movement_only_text_is_outside_iron_pit_combat_math_scope() -> None:
    assert not combat_math_relevant("The target's Speed decreases by 10 feet until the end of its next turn.")
    assert not combat_math_relevant("The creature teleports up to 60 feet to an unoccupied space it can see.")
    assert not combat_math_relevant("The target is pushed up to 15 feet straight away from the creature.")


def test_outcome_changing_text_stays_in_scope() -> None:
    assert combat_math_relevant("The target has Disadvantage on the next attack roll it makes.")
    assert combat_math_relevant("The creature adds 2 to the roll.")
    assert combat_math_relevant("The target can't take a Reaction until the end of its next turn.")
    assert combat_math_relevant("The target has the Prone condition.")


def test_feature_blocks_use_reviewed_headings_instead_of_guessing_prose() -> None:
    source = "Earth Glide. The creature moves through earth and stone. Magic Resistance. The creature has Advantage on saving throws against spells."
    headings = ["Earth Glide", "Magic Resistance"]
    blocks = feature_blocks(source, headings)
    assert blocks["Earth Glide"].startswith("Earth Glide.")
    assert "Magic Resistance" not in blocks["Earth Glide"]
    assert blocks["Magic Resistance"].startswith("Magic Resistance.")


def test_trait_scope_ignores_movement_but_keeps_save_math() -> None:
    source = "Earth Glide. The creature can move through nonmagical earth and stone. Magic Resistance. The creature has Advantage on saving throws against spells and other magical effects."
    assert combat_relevant_trait_names(source) == {"Magic Resistance"}


def test_bonus_action_scope_ignores_teleport_only() -> None:
    source = "Teleport (Recharge 4-6). The blink dog teleports up to 40 feet to an unoccupied space it can see."
    assert arena_neutral_bonus_action_source(source)


def test_reaction_scope_ignores_audible_or_movement_only_but_not_roll_math() -> None:
    audible = "Shriek. Trigger: A creature or a light source moves within 30 feet of the shrieker. Response: The shrieker emits a shriek audible within 300 feet of itself for 1 minute or until the shrieker dies."
    pursuit = "Pursuit. Trigger: Another creature the nalfeshnee can see ends its move within 120 feet of the nalfeshnee. Response: The nalfeshnee teleports to an unoccupied space within 10 feet of the triggering creature."
    ingenuity = "Burst of Ingenuity (2/Day). Trigger: The sphinx or another creature within 30 feet makes an ability check or a saving throw. Response: The sphinx adds 2 to the roll."
    assert arena_neutral_reaction_source(audible)
    assert arena_neutral_reaction_source(pursuit)
    assert not arena_neutral_reaction_source(ingenuity)


def test_limited_use_scope_ignores_limited_movement_but_keeps_limited_damage() -> None:
    movement_row = {
        "traits": "",
        "actions": "",
        "bonusActions": "Teleport (3/Day). The creature teleports up to 40 feet.",
        "reactions": "",
    }
    damage_row = {
        "traits": "",
        "actions": "Burst (1/Day). Each creature in the area takes 10 Force damage.",
        "bonusActions": "",
        "reactions": "",
    }
    movement_name = parse_limited_use_names(movement_row)[0]
    damage_name = parse_limited_use_names(damage_row)[0]
    assert not limited_use_source_relevant(movement_row, movement_name)
    assert limited_use_source_relevant(damage_row, damage_name)


def test_legendary_scope_ignores_move_only_but_keeps_extra_attack() -> None:
    move_only = "Legendary Action Uses: 3. The creature regains all expended uses at the start of each of its turns. Move. The creature moves up to half its Speed."
    pounce = "Legendary Action Uses: 3. The creature regains all expended uses at the start of each of its turns. Pounce. The creature moves up to half its Speed, and it makes one Rend attack."
    assert not legendary_source_relevant(move_only)
    assert legendary_source_relevant(pounce)
