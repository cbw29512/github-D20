(() => {
  "use strict";
  const S = () => window.IRON_PIT_BROWSER_STATE;
  const R = () => window.IRON_PIT_BROWSER_ROLLS;
  const T = () => window.IRON_PIT_BROWSER_TURN;
  const L = () => window.IRON_PIT_BROWSER_CONDITION_LIFECYCLE;
  const P = () => window.IRON_PIT_BROWSER_PRECOMBAT_SPELLS;
  const C = () => window.IRON_PIT_BROWSER_CONCENTRATION, B = () => window.IRON_PIT_BROWSER_SOURCE_BOUND_EFFECTS, Z = () => window.IRON_PIT_BROWSER_RECHARGE;
  const F = () => window.IRON_PIT_BROWSER_FORMATION;
  const Q = () => window.IRON_PIT_BROWSER_CONDITION_RULES || { incapacitated: (state) => state.is_unconscious };
  const heroes = () => window.IRON_PIT_BROWSER_HEROES;
  const monsters = () => window.IRON_PIT_BROWSER_MONSTERS;

  function cloneTemplate(template) { return structuredClone(template); }

  function buildSetup(selection) {
    const heroMembers = selection.hero_ids.map((id, index) => {
      if (!heroes()[id]) throw new Error(`Unknown certified hero: ${id}`);
      const template = cloneTemplate(heroes()[id]);
      return { combatant_id: `hero-${index + 1}:${id}`, side: "heroes", position_ft: F().startingPosition(template, "heroes"), state: S().buildState(template) };
    });
    const monsterMembers = selection.monster_ids.map((id, index) => {
      if (!monsters()[id]) throw new Error(`Unknown certified monster: ${id}`);
      const template = cloneTemplate(monsters()[id]);
      return { combatant_id: `monster-${index + 1}:${id}`, side: "monsters", position_ft: F().startingPosition(template, "monsters"), state: S().buildState(template) };
    });
    return {
      heroes: heroMembers,
      monsters: monsterMembers,
      hero_total_levels: heroMembers.reduce((sum, item) => sum + item.state.template.level, 0),
      monster_total_cr: totalCr(monsterMembers.map((item) => item.state.template.challenge_rating)),
    };
  }

  function crNumber(value) {
    const text = String(value || "0");
    if (!text.includes("/")) return Number(text) || 0;
    const [a, b] = text.split("/").map(Number); return a / b;
  }

  function totalCr(values) {
    const quarters = Math.round(values.reduce((sum, value) => sum + crNumber(value), 0) * 4);
    if (quarters % 4 === 0) return String(quarters / 4);
    const divisor = quarters % 2 === 0 ? 2 : 4;
    return `${quarters / (4 / divisor)}/${divisor}`;
  }

  function initiative(setup) {
    const groups = setup.heroes.map((member, index) => ({ side: "heroes", template_id: member.state.template.id, members: [member], index }));
    const byTemplate = new Map();
    setup.monsters.forEach((member, index) => {
      const key = member.state.template.id;
      if (!byTemplate.has(key)) byTemplate.set(key, { side: "monsters", template_id: key, members: [], index: setup.heroes.length + index });
      byTemplate.get(key).members.push(member);
    });
    groups.push(...byTemplate.values());
    for (const group of groups) {
      const state = group.members[0].state, advantage = Boolean(state.template.initiative_advantage), disadvantage = Q().incapacitated(state);
      const mode = advantage === disadvantage ? "normal" : advantage ? "advantage" : "disadvantage";
      const roll = R().d20(state.template.initiative_bonus, mode);
      group.initiative_roll = roll; group.natural_roll = roll.selected_roll;
      group.initiative_bonus = state.template.initiative_bonus;
      group.initiative_count = roll.total;
      group.tie_break_roll = null;
      group.members.forEach((member) => {
        member.state.initiative_roll = roll.selected_roll;
        member.state.initiative_total = roll.total;
      });
    }
    const tiedCounts = new Map();
    groups.forEach((group) => { const list = tiedCounts.get(group.initiative_count) || []; list.push(group); tiedCounts.set(group.initiative_count, list); });
    for (const tied of tiedCounts.values()) {
      if (new Set(tied.map((item) => item.side)).size < 2) continue;
      const arena = window.IRON_PIT_DICE.roll(20);
      tied.forEach((group) => { group.tie_break_roll = group.side === "heroes" ? arena : 21 - arena; });
    }
    groups.sort((a, b) => b.initiative_count - a.initiative_count || (b.tie_break_roll || 0) - (a.tie_break_roll || 0) || a.index - b.index);
    return {
      groups: groups.map((group) => ({ side: group.side, template_id: group.template_id, combatant_ids: group.members.map((m) => m.combatant_id), initiative_roll: group.initiative_roll, natural_roll: group.natural_roll, initiative_bonus: group.initiative_bonus, initiative_count: group.initiative_count, tie_break_roll: group.tie_break_roll })),
      turn_order: groups.flatMap((group) => group.members.map((member) => member.combatant_id)),
    };
  }

  function defeatedMember(member) {
    const state = member.state;
    if (state.template.kind === "character") return state.is_dead || !state.is_alive;
    return state.current_hp <= 0 || state.is_dead || !state.is_alive;
  }

  function outcome(setup) {
    const defeated = (side) => side.every(defeatedMember);
    const heroesDead = defeated(setup.heroes), monstersDead = defeated(setup.monsters);
    if (heroesDead && monstersDead) return "draw";
    if (monstersDead) return "heroes_win";
    if (heroesDead) return "monsters_win";
    return "active";
  }

  function initiativeEvents(init, setup, startSequence = 1) {
    const all = [...setup.heroes, ...setup.monsters];
    const names = new Map(all.map((member) => [member.combatant_id, member.state.template.name]));
    let sequence = startSequence;
    return init.groups.map((group) => ({ sequence: sequence++, round_number: 0, event_type: "initiative", actor_id: group.combatant_ids[0], actor_name: names.get(group.combatant_ids[0]), attack_roll: group.initiative_roll, animation: "initiative", description: `${names.get(group.combatant_ids[0])}${group.combatant_ids.length > 1 ? ` group (${group.combatant_ids.length})` : ""} rolls initiative ${group.initiative_count}.` }));
  }

  function lifecycle(sequence, round, member, setup, targetTiming, sourceTiming) {
    const target = L().resolveTargetTiming(sequence, round, member, targetTiming);
    const source = L().resolveSourceTiming(target.sequence, round, member, setup, sourceTiming);
    if (sourceTiming === "source_turn_end") {
      const states = [...setup.heroes, ...setup.monsters].map((entry) => entry.state);
      window.IRON_PIT_BROWSER_MODIFIERS?.expireSourceTurn(states, member.combatant_id, round);
    }
    return { events: [...target.events, ...source.events], sequence: source.sequence };
  }

  function runEncounter(selection) {
    if (!selection.hero_ids?.length || !selection.monster_ids?.length || selection.hero_ids.length > 6 || selection.monster_ids.length > 6) throw new Error("Iron Pit requires 1-6 cards per side.");
    const setup = buildSetup(selection);
    const prep = P()?.prepare(setup, 1) || { events: [], sequence: 1 };
    const init = initiative(setup);
    const members = [...setup.heroes, ...setup.monsters], states = members.map((member) => member.state);
    const byId = new Map(members.map((member) => [member.combatant_id, member]));
    const events = [...prep.events, ...initiativeEvents(init, setup, prep.sequence)]; let sequence = events.length + 1; let resolvedRound = 0;
    for (let round = 1; round <= 100; round += 1) {
      resolvedRound = round;
      for (const id of init.turn_order) {
        const current = outcome(setup); if (current !== "active") return finish(setup, init, events, current, round, sequence);
        const member = byId.get(id);
        B()?.cleanupDisabledSources(setup); window.IRON_PIT_BROWSER_MODIFIERS?.expireSourceTurnStart(states, member.combatant_id); S().refreshStartOfTurn(member.state); const recharge = Z()?.resolve(sequence, round, member); if (recharge) { events.push(...recharge.events); sequence = recharge.sequence; } C()?.endIfExpired(member.state, round, states);
        const start = lifecycle(sequence, round, member, setup, "target_turn_start", "source_turn_start");
        events.push(...start.events); sequence = start.sequence;
        if (member.state.template.kind === "character" && member.state.current_hp === 0 && !member.state.is_dead && !member.state.is_stable) events.push(T().deathSave(sequence++, round, member));
        if (member.state.current_hp > 0 && !member.state.is_dead) {
          const turn = T().resolveTurn(sequence, round, member, setup); events.push(...turn.events); sequence = turn.sequence;
        }
        const end = lifecycle(sequence, round, member, setup, "target_turn_end", "source_turn_end");
        events.push(...end.events); sequence = end.sequence;
      }
      const current = outcome(setup); if (current !== "active") return finish(setup, init, events, current, round, sequence);
    }
    return finish(setup, init, events, "draw", resolvedRound, sequence);
  }

  function finish(setup, init, events, result, round, sequence) {
    events.push({ sequence, round_number: round, event_type: result === "draw" ? "draw" : "victory", actor_id: "arena", actor_name: "Iron Pit", animation: "victory", description: result === "heroes_win" ? "Heroes win the deathmatch." : result === "monsters_win" ? "Monsters win the deathmatch." : "The fight reaches the arena round limit and ends in a draw." });
    return { battle_id: crypto.randomUUID?.() || `battle-${Date.now()}`, outcome: result, rounds: round, setup, initiative: init, events, ruleset: "SRD 5.2.1 Iron Pit formation deathmatch subset" };
  }

  window.IRON_PIT_BROWSER_ENGINE = { runEncounter };
})();
