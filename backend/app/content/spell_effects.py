from __future__ import annotations

from app.domain.spells import DefensiveSpellAction, SpellModifierEffect


BLESS = DefensiveSpellAction(
    id="bless",
    name="Bless",
    level=1,
    action_cost="action",
    range_ft=30,
    duration_minutes=1,
    target_policy="friendly",
    target_count=3,
    modifier_effects=[
        SpellModifierEffect(kind="attack-roll-bonus-die", dice_count=1, dice_size=4),
        SpellModifierEffect(kind="saving-throw-bonus-die", dice_count=1, dice_size=4),
    ],
    concentration=True,
    priority=30,
    animation="bless",
    source="SRD 5.2.1 Bless",
)

SHIELD_OF_FAITH = DefensiveSpellAction(
    id="shield-of-faith",
    name="Shield of Faith",
    level=1,
    action_cost="bonus_action",
    range_ft=60,
    duration_minutes=10,
    modifier_effects=[SpellModifierEffect(kind="armor-class", flat_bonus=2)],
    concentration=True,
    priority=20,
    animation="shield-of-faith",
    source="SRD 5.2.1 p.162",
)

AID = DefensiveSpellAction(
    id="aid",
    name="Aid",
    level=2,
    action_cost="action",
    range_ft=30,
    duration_minutes=480,
    target_policy="friendly",
    target_count=3,
    max_hp_increase=5,
    current_hp_increase=5,
    priority=40,
    animation="aid",
    source="D&D Beyond Basic Rules 2024: Aid",
)


def defensive_spell_by_id(spell_id: str) -> DefensiveSpellAction:
    spells = {spell.id: spell for spell in (BLESS, SHIELD_OF_FAITH, AID)}
    try:
        return spells[spell_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported certified defensive spell: {spell_id}") from exc
