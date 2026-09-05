from app.content.monster_survival_source_audit import survival_action_issues


def test_hit_point_maximum_reduction_fails_closed() -> None:
    actions = (
        "Life Drain. Melee Attack Roll: +4, reach 5 ft. Hit: 7 (2d6) Necrotic damage. "
        "If the target is a creature, its Hit Point maximum decreases by an amount equal to the damage taken."
    )
    assert survival_action_issues(actions) == [
        "unsupported-survival-rider:hit-point-maximum-reduction"
    ]


def test_hit_point_maximum_reduction_tolerates_source_line_breaks() -> None:
    actions = "The target’s Hit Point maximum\n\ndecreases by an amount equal to the Necrotic damage taken."
    assert survival_action_issues(actions) == [
        "unsupported-survival-rider:hit-point-maximum-reduction"
    ]


def test_combatant_creation_action_fails_closed() -> None:
    actions = (
        "Create Specter. The wraith targets a Humanoid corpse within 10 feet. "
        "The target's spirit rises as a Specter in the nearest unoccupied space."
    )
    assert survival_action_issues(actions) == ["unsupported-combatant-creation-action"]


def test_plain_damage_attack_has_no_survival_rider_issue() -> None:
    actions = "Bite. Melee Attack Roll: +4, reach 5 ft. Hit: 7 (2d4 + 2) Piercing damage."
    assert survival_action_issues(actions) == []
