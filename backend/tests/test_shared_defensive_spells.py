from app.content.spell_effects import defensive_spell_by_id


def test_aid_is_shared_nonconcentration_hp_buff() -> None:
    aid = defensive_spell_by_id("aid")
    assert aid.level == 2
    assert aid.action_cost == "action"
    assert aid.range_ft == 30
    assert aid.target_policy == "friendly"
    assert aid.target_count == 3
    assert (aid.max_hp_increase, aid.current_hp_increase) == (5, 5)
    assert aid.concentration is False


def test_existing_defensive_spells_remain_available() -> None:
    assert defensive_spell_by_id("bless").concentration is True
    assert defensive_spell_by_id("shield-of-faith").action_cost == "bonus_action"


def test_unknown_defensive_spell_fails_closed() -> None:
    try:
        defensive_spell_by_id("death-ward")
    except ValueError as exc:
        assert "Unsupported certified defensive spell" in str(exc)
    else:
        raise AssertionError("Unaudited defensive spell must fail closed.")
