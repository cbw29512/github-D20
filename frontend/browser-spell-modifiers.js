(() => {
  "use strict";

  const M = () => window.IRON_PIT_BROWSER_MODIFIERS;
  const C = () => window.IRON_PIT_BROWSER_CONCENTRATION;

  function build(sourceId, targetId, spell, effect, index, roundNumber = null) {
    let expiry = null;
    if (effect.expiresAfterSourceTurns != null) {
      if (roundNumber == null) throw new Error("Source-turn modifier expiry requires the application round.");
      expiry = roundNumber + effect.expiresAfterSourceTurns;
    }
    return {
      id: `${sourceId}:${spell.id}:${targetId}:${index}`,
      source_id: sourceId,
      source_effect_id: spell.id,
      kind: effect.kind,
      flat_bonus: effect.flatBonus || 0,
      dice_count: effect.diceCount || 0,
      dice_size: effect.diceSize || 0,
      damage_type: effect.damageType || null,
      target_id: targetId,
      concentration_required: Boolean(spell.concentration),
      consume_on_attack_against: Boolean(effect.consumeOnAttackAgainst),
      expires_at_end_of_target_turn: Boolean(effect.expiresAtEndOfTargetTurn),
      expires_source_turn_end_round: expiry,
    };
  }

  function apply(owner, targets, sourceId, spell, roundNumber, states = []) {
    const modifiers = targets.flatMap(({ targetId }) => (spell.modifierEffects || [])
      .map((effect, index) => build(sourceId, targetId, spell, effect, index, roundNumber)));
    if (spell.concentration) {
      if (!C()) throw new Error("Browser Concentration runtime is not loaded.");
      const durationRounds = spell.durationMinutes * 10;
      const expiresRound = roundNumber + durationRounds + (roundNumber === 0 ? 1 : 0);
      C().start(owner, sourceId, spell.id, roundNumber, states, expiresRound);
    }
    for (const { targetId, state } of targets) {
      (spell.modifierEffects || []).forEach((effect, index) => M().add(state, build(sourceId, targetId, spell, effect, index, roundNumber)));
    }
    return modifiers;
  }

  window.IRON_PIT_BROWSER_SPELL_MODIFIERS = { apply, build };
})();
