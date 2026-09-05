(() => {
  "use strict";

  const R = () => window.IRON_PIT_BROWSER_ROLLS;
  const A = () => window.IRON_PIT_BROWSER_ATTACK;
  const G = () => window.IRON_PIT_BROWSER_GRAPPLE;
  const S = () => window.IRON_PIT_BROWSER_STATE;
  const X = () => window.IRON_PIT_BROWSER_RESOURCES;
  const F = () => window.IRON_PIT_BROWSER_FORMATION;
  const B2 = () => window.IRON_PIT_BROWSER_BARBARIAN2 || { dangerSenseAdvantage: () => 0 };
  const M = () => window.IRON_PIT_BROWSER_MODIFIERS || { applyD20Bonus: (_state, _kind, roll) => roll };
  const C = () => window.IRON_PIT_BROWSER_CONCENTRATION;
  const D = () => window.IRON_PIT_DICE;
  const E = () => window.IRON_PIT_ACTION_ECONOMY || { available: (state, cost) => cost === "action" && state.action_available, spend: (state) => { state.action_available = false; } };
  const Q = () => window.IRON_PIT_BROWSER_CONDITION_RULES || { autoFailStrDex: (state) => state.is_unconscious };
  const states = (setup) => setup ? [...setup.heroes, ...setup.monsters].map((member) => member.state) : [];
  const BOARD_COLUMNS = 3, MAX_BOARD_SLOTS = 6;

  function saveMode(state, ability) {
    const advantage = (ability === "strength" && state.active_effect_ids.includes("rage") ? 1 : 0) + B2().dangerSenseAdvantage(state, ability);
    const disadvantage = ability === "dexterity" && state.active_effect_ids.includes("restrained") ? 1 : 0;
    return R().modeFromSources(advantage, disadvantage);
  }

  function resolveSavingThrow(state, ability, dc) {
    if ((ability === "strength" || ability === "dexterity") && Q().autoFailStrDex(state)) return { roll: null, succeeded: false };
    const bonus = state.template.saving_throw_bonuses?.[ability];
    if (bonus == null) throw new Error(`${state.template.name} lacks a certified ${ability} saving throw bonus.`);
    let roll = M().applyD20Bonus(state, "saving-throw-bonus-die", R().d20(bonus, saveMode(state, ability)));
    if (roll.total < dc) { const reroll = window.IRON_PIT_BROWSER_INDOMITABLE?.use(state, ability); if (reroll) roll = reroll; }
    return { roll, succeeded: roll.total >= dc };
  }

  function resourceAvailable(state, action) { return !action.resourceId || X().available(state, action.resourceId, action.resourceCost || 1); }
  function legalAction(action, target, distance) { return distance <= action.range && (!action.targetMaxSize || S().sizeAtMost(target, action.targetMaxSize)); }

  function damageRolls(action, count, shared) {
    if (shared == null) return D().rollMany(count, action.damageDiceSize);
    if (!Array.isArray(shared) || shared.length !== count) throw new Error(`${action.name} shared damage roll count is invalid.`);
    if (shared.some((roll) => !Number.isInteger(roll) || roll < 1 || roll > action.damageDiceSize)) throw new Error(`${action.name} shared damage rolls contain an invalid die result.`);
    return [...shared];
  }

  function resolveAction(sequence, round, actor, target, action, distance, options = {}) {
    const spendAction = options.spendAction !== false, spendResource = options.spendResource !== false;
    if (spendAction && !E().available(actor.state, "action")) throw new Error("Action is unavailable for saving throw action.");
    if (spendResource && !resourceAvailable(actor.state, action)) throw new Error(`${action.name} resource is unavailable.`);
    if (!legalAction(action, target, distance)) throw new Error(`${action.name} has no legal target at ${distance} feet.`);
    const save = resolveSavingThrow(target.state, action.saveAbility, action.dc);
    if (spendAction) E().spend(actor.state, "action");
    if (spendResource && action.resourceId) X().spend(actor.state, action.resourceId, action.resourceCost || 1);
    const hpBefore = target.state.current_hp, temporaryHpBefore = target.state.temporary_hp;
    const deathSuccessBefore = target.state.death_save_successes, deathFailureBefore = target.state.death_save_failures;
    const concentrationBefore = target.state.concentration?.effect_id || null;
    let damageRoll = null, damageComponents = [], damageOutcome = null;
    const count = action.damageDiceCount || 0;
    if (count && !(save.succeeded && action.successDamage === "none")) {
      if (!action.damageType) throw new Error(`${action.name} has damage dice but no damage type.`);
      const rolls = damageRolls(action, count, options.sharedDamageRolls);
      let total = rolls.reduce((sum, roll) => sum + roll, 0) + (action.damageBonus || 0);
      if (save.succeeded && action.successDamage === "half") total = Math.floor(total / 2);
      const applied = A().adjustedDamage(target.state, Math.max(0, total), action.damageType);
      damageComponents = [{ source: action.name, notation: `${count}d${action.damageDiceSize}+${action.damageBonus || 0}`, rolls, modifier: action.damageBonus || 0, damage_type: action.damageType, total: Math.max(0, total), applied_total: applied }];
      damageRoll = { notation: damageComponents[0].notation, rolls, modifier: action.damageBonus || 0, total: applied };
      if (applied) {
        const affectedStates = states(options.setup); damageOutcome = A().applyDamage(target.state, applied, false, [action.damageType], affectedStates);
        window.IRON_PIT_BROWSER_RAGE?.endIfIncapacitated?.(target.state); C()?.endIfIncapacitated?.(target.state, affectedStates);
      }
    }
    let appliedConditions = [];
    if (!save.succeeded && target.state.is_alive && !target.state.is_dead && action.grappleEscapeDc) appliedConditions = G().apply(target.state, actor.combatant_id, action.grappleEscapeDc, action.range, Boolean(action.restrainsWhileGrappled));
    let description = `${target.state.template.name} ${save.succeeded ? "SUCCEEDS" : "FAILS"} a DC ${action.dc} ${action.saveAbility} save against ${actor.state.template.name}'s ${action.name}.`;
    if (damageOutcome === "undead_fortitude") description += ` ${target.state.template.name} succeeds on Undead Fortitude and remains at 1 HP.`;
    if (appliedConditions.includes("grappled")) description += ` ${target.state.template.name} is Grappled.`;
    if (appliedConditions.includes("restrained")) description += ` ${target.state.template.name} is Restrained while Grappled.`;
    return { sequence, round_number: round, event_type: "saving_throw", actor_id: actor.combatant_id, actor_name: actor.state.template.name,
      target_id: target.combatant_id, target_name: target.state.template.name, saving_throw_roll: save.roll, save_ability: action.saveAbility, save_dc: action.dc,
      save_succeeded: save.succeeded, damage_roll: damageRoll, damage_components: damageComponents, applied_condition_ids: appliedConditions,
      hp_before: hpBefore, hp_after: target.state.current_hp, temporary_hp_before: temporaryHpBefore, temporary_hp_after: target.state.temporary_hp,
      death_save_successes_before: deathSuccessBefore, death_save_failures_before: deathFailureBefore, death_save_successes: target.state.death_save_successes,
      death_save_failures: target.state.death_save_failures, is_stable: target.state.is_stable, is_dead: target.state.is_dead, feature_id: action.id,
      resource_remaining: action.resourceId ? X().uses(actor.state, action.resourceId) : null,
      concentration_ended_effect_id: concentrationBefore && !target.state.concentration ? concentrationBefore : null,
      animation: action.animation || "save-effect", description };
  }

  const living = (member) => member.state.is_alive && !member.state.is_dead && member.state.current_hp > 0;
  const rows = (actor, setup) => actor.side === "heroes" ? [setup.monsters, setup.heroes] : [setup.heroes, setup.monsters];
  const forward = (actor, member) => (actor.side === "heroes" ? 1 : -1) * (member.position_ft - actor.position_ft);
  const columnFor = (index) => { if (index < 0 || index >= MAX_BOARD_SLOTS) throw new Error("board slot index out of range"); return index % BOARD_COLUMNS; };
  function lineTargets(actor, setup, action, enemies, friends, order) {
    if (action.area.widthFt !== 5) throw new Error(`${action.name} Line widths above 5 feet are not runtime-certified.`);
    const actorIndex = friends.findIndex((member) => member.combatant_id === actor.combatant_id);
    const column = columnFor(actorIndex);
    const exposed = friends.some((member, index) => member.combatant_id !== actor.combatant_id && columnFor(index) === column
      && living(member) && forward(actor, member) > 0 && forward(actor, member) <= action.area.sizeFt);
    if (exposed) return [];
    return enemies.filter((member, index) => columnFor(index) === column && living(member)
      && forward(actor, member) > 0 && forward(actor, member) <= action.area.sizeFt
      && legalAction(action, member, F().saveDistance(actor, member, action.range)))
      .sort((a, b) => (order[a.combatant_id] ?? MAX_BOARD_SLOTS) - (order[b.combatant_id] ?? MAX_BOARD_SLOTS));
  }
  function targetsFor(actor, setup, action) {
    if (!action.area) {
      for (const target of F().targetOrder(actor, setup)) if (legalAction(action, target, F().saveDistance(actor, target, action.range))) return [target];
      return [];
    }
    if (!['cone', 'line'].includes(action.area.shape)) throw new Error(`${action.name} area shape is not runtime-certified.`);
    const [enemies, friends] = rows(actor, setup);
    const order = Object.fromEntries(F().targetOrder(actor, setup).map((member, index) => [member.combatant_id, index]));
    if (action.area.shape === 'line') return lineTargets(actor, setup, action, enemies, friends, order);
    const width = action.area.sizeFt;
    if (!width || width % 5) throw new Error(`${action.name} area width must use 5-foot card increments.`);
    const slotCount = Math.min(MAX_BOARD_SLOTS, Math.max(1, width / 5)), candidates = [];
    for (let start = 0; start <= MAX_BOARD_SLOTS - slotCount; start += 1) {
      const targets = enemies.filter((member, index) => start <= index && index < start + slotCount && living(member)
        && forward(actor, member) > 0 && forward(actor, member) <= action.area.sizeFt
        && legalAction(action, member, F().saveDistance(actor, member, action.range)));
      const exposed = friends.some((member, index) => member.combatant_id !== actor.combatant_id && start <= index && index < start + slotCount
        && living(member) && forward(actor, member) > 0 && forward(actor, member) <= action.area.sizeFt);
      if (targets.length && !exposed) candidates.push({ start, targets: targets.sort((a, b) => (order[a.combatant_id] ?? MAX_BOARD_SLOTS) - (order[b.combatant_id] ?? MAX_BOARD_SLOTS)) });
    }
    candidates.sort((a, b) => b.targets.length - a.targets.length || a.start - b.start);
    return candidates[0]?.targets || [];
  }

  function resolveTurnAction(sequence, round, actor, setup, resourceBackedOnly) {
    if (!E().available(actor.state, "action")) return { events: [], sequence, used: false };
    for (const action of actor.state.template.saving_throw_actions || []) {
      if (resourceBackedOnly !== Boolean(action.resourceId) || !resourceAvailable(actor.state, action)) continue;
      const targets = targetsFor(actor, setup, action); if (!targets.length) continue;
      const events = []; let shared = null;
      targets.forEach((target, index) => {
        const event = resolveAction(sequence++, round, actor, target, action, F().saveDistance(actor, target, action.range), {
          spendAction: index === 0, spendResource: index === 0, sharedDamageRolls: shared, setup,
        });
        events.push(event); if (!shared && event.damage_components?.length) shared = [...event.damage_components[0].rolls];
      });
      return { events, sequence, used: true };
    }
    return { events: [], sequence, used: false };
  }

  window.IRON_PIT_BROWSER_SAVES = { legalAction, resourceAvailable, resolveAction, resolveSavingThrow, resolveTurnAction, saveMode, targetsFor };
})();
