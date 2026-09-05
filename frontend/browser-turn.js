(() => {
  "use strict";
  const S = () => window.IRON_PIT_BROWSER_STATE, C = () => window.IRON_PIT_BROWSER_CHARGE;
  const M = () => window.IRON_PIT_BROWSER_MULTIATTACK, G = () => window.IRON_PIT_BROWSER_RAGE;
  const J = () => window.IRON_PIT_BROWSER_ACTION_SURGE, P = () => window.IRON_PIT_BROWSER_SUPPORT;
  const T = () => window.IRON_PIT_BROWSER_TACTICAL_SHIFT, O = () => window.IRON_PIT_BROWSER_ONGOING_SPELL_CONTROL;
  const L = () => window.IRON_PIT_BROWSER_SPELL_OFFENSE, U = () => window.IRON_PIT_BROWSER_STANDARD_ATTACK_ACTION;
  const F = () => window.IRON_PIT_BROWSER_FORMATION;
  const NO_SAVE = { resolveTurnAction: (sequence) => ({ events: [], sequence, used: false }) };
  const V = () => window.IRON_PIT_BROWSER_SAVES?.resolveTurnAction ? window.IRON_PIT_BROWSER_SAVES : NO_SAVE;
  const D = () => window.IRON_PIT_DICE;
  const E = () => window.IRON_PIT_ACTION_ECONOMY || { available: (s, c) => c === "action" ? s.action_available : s.bonus_action_available };
  const NO_CONTROL = { cleanup: () => {}, shouldEscape: () => false };
  const H = () => window.IRON_PIT_BROWSER_GRAPPLE || NO_CONTROL;

  function enablePitRangePolicy() {
    const rolls = window.IRON_PIT_BROWSER_ROLLS;
    if (!rolls || rolls.fixedFormationActive) return;
    const rawAttackMode = rolls.attackMode;
    rolls.attackMode = (attack, distance, advantage = 0, disadvantage = 0) => rawAttackMode(attack, distance, advantage, disadvantage, false);
    rolls.fixedFormationActive = true;
  }

  function deathSave(sequence, round, member) {
    const state = member.state, natural = D().roll(20);
    const successesBefore = state.death_save_successes, failuresBefore = state.death_save_failures;
    let result = "failure";
    if (natural === 20) {
      state.current_hp = 1; state.is_alive = true; state.is_unconscious = false; state.is_stable = false;
      state.death_save_successes = 0; state.death_save_failures = 0; result = "natural 20; regains 1 HP";
    } else if (natural === 1) {
      state.death_save_failures = Math.min(3, state.death_save_failures + 2); result = "natural 1; two failures";
    } else if (natural >= 10) {
      state.death_save_successes = Math.min(3, state.death_save_successes + 1); result = "success";
    } else state.death_save_failures = Math.min(3, state.death_save_failures + 1);
    if (state.death_save_failures >= 3) result += "; dies";
    if (state.death_save_failures >= 3) {
      state.is_alive = false; state.is_dead = true; state.is_unconscious = false; state.is_stable = false;
    } else if (state.death_save_successes >= 3) {
      state.is_stable = true; state.is_unconscious = true; state.death_save_successes = 0; state.death_save_failures = 0; result = "third success; becomes Stable";
    }
    return { sequence, round_number: round, event_type: "death_save", actor_id: member.combatant_id, actor_name: state.template.name,
      death_save_roll: { notation: "1d20", rolls: [natural], selected_roll: natural, modifier: 0, mode: "normal", total: natural },
      hp_after: state.current_hp, death_save_successes_before: successesBefore, death_save_failures_before: failuresBefore,
      death_save_successes: state.death_save_successes, death_save_failures: state.death_save_failures,
      is_stable: state.is_stable, is_dead: state.is_dead, animation: "death-save", description: `${state.template.name} makes a Death Save: ${result}.` };
  }

  function finalize(events, sequence, round, member, setup, turnKey, allowSurge = true) {
    const surge = allowSurge ? J()?.resolveAttack(sequence, round, member, setup, turnKey) : null;
    if (surge) { events.push(...surge.events); sequence = surge.sequence; }
    const rage = G()?.finalize(sequence, round, member); if (rage?.event) events.push(rage.event);
    return { events, sequence: rage?.sequence ?? sequence };
  }

  function resolveTurn(sequence, round, member, setup) {
    enablePitRangePolicy();
    const events = []; H().cleanup(setup); S().beginTurn(member.state);
    const turnKey = `${round}:${member.combatant_id}`;
    if (O()?.forcedRetreatActive(member.state)) {
      events.push(O().event(sequence++, round, member)); return finalize(events, sequence, round, member, setup, turnKey, false);
    }
    const support = P()?.resolve(sequence, round, member, setup, turnKey);
    if (support) { events.push(...support.events); sequence = support.sequence; }
    const rage = G()?.enter(sequence, round, member); if (rage) { events.push(rage); sequence += 1; }
    const wind = P()?.secondWind(sequence, round, member);
    if (wind) { events.push(wind); sequence += 1; const shift = T()?.resolve(sequence, round, member, setup); if (shift) { events.push(shift); sequence += 1; } }
    if (H().shouldEscape(member.state)) { events.push(H().escape(sequence++, round, member)); return finalize(events, sequence, round, member, setup, turnKey); }
    const rush = P()?.adrenaline(sequence, round, member); if (rush) { events.push(rush); sequence += 1; }
    const spell = L()?.resolve(sequence, round, member, setup, turnKey);
    if (spell) { events.push(...spell.events); sequence = spell.sequence; }
    if (!E().available(member.state, "action")) return finalize(events, sequence, round, member, setup, turnKey);

    const targets = F().targetOrder(member, setup);
    if (!targets.length) return finalize(events, sequence, round, member, setup, turnKey);
    const charged = C()?.resolveClosing(sequence, round, member, targets[0], setup);
    if (charged?.handled) { events.push(...charged.events); return finalize(events, charged.sequence, round, member, setup, turnKey); }

    const resourceAttack = F().chooseResourceBackedAttack?.(member, setup) || null;
    if (resourceAttack) {
      const limited = U().resolve(sequence, round, member, resourceAttack.target, resourceAttack.attack, resourceAttack.distance, setup, turnKey, {
        featureId: resourceAttack.attack.resourceId,
      });
      events.push(...limited.events); return finalize(events, limited.sequence, round, member, setup, turnKey);
    }

    const limitedSave = V().resolveTurnAction(sequence, round, member, setup, true);
    if (limitedSave.used) { events.push(...limitedSave.events); return finalize(events, limitedSave.sequence, round, member, setup, turnKey); }
    if (member.state.template.attack_action) {
      const multi = M().resolveAttackAction(sequence, round, member, setup); events.push(...multi.events);
      return finalize(events, multi.sequence, round, member, setup, turnKey);
    }
    const saved = V().resolveTurnAction(sequence, round, member, setup, false);
    if (saved.used) { events.push(...saved.events); return finalize(events, saved.sequence, round, member, setup, turnKey); }
    const choice = F().chooseStandardAttack(member, setup);
    if (choice && E().available(member.state, "action")) {
      const pack = S().packTactics(member, setup), opener = C()?.openingFeature?.(round, member, setup) || null;
      const standard = U().resolve(sequence, round, member, choice.target, choice.attack, choice.distance, setup, turnKey, {
        advantage: pack ? 1 : 0, featureId: opener || (pack ? "pack-tactics" : null),
      });
      events.push(...standard.events); sequence = standard.sequence;
    }
    return finalize(events, sequence, round, member, setup, turnKey);
  }

  window.IRON_PIT_BROWSER_TURN = { deathSave, resolveTurn };
})();
