(() => {
  "use strict";

  const E = () => window.IRON_PIT_ACTION_ECONOMY;
  const C = () => window.IRON_PIT_BROWSER_SPELLCASTING;
  const R = () => window.IRON_PIT_BROWSER_CONDITION_REMOVAL;
  const S = () => window.IRON_PIT_BROWSER_STATE;
  const bloodied = (state) => state.current_hp * 2 <= S().effectiveMaxHp(state);
  const distance = (a, b) => Math.abs(a.position_ft - b.position_ft);
  const swarm = (state) => state.template.traits?.includes("swarm");
  const slotHeal = (action) => Boolean(action.resourceId?.startsWith("spell-slot-"));
  const removable = (target, action) => target.state.active_effect_ids.filter((id) => (action.removableConditions || []).includes(id));

  function resourceAvailable(member, action, turnKey = null) {
    if (!action.resourceId) return true;
    if (slotHeal(action) && (!turnKey || !C().slotSpellAvailable(member.state, turnKey))) return false;
    return (member.state.resources[action.resourceId] || 0) >= (action.resourceCost || 1);
  }

  function targetAllowed(healer, target, action) {
    if (target.state.is_dead || !target.state.is_alive || swarm(target.state)) return false;
    if (distance(healer, target) > (action.range || 5)) return false;
    if (target.state.current_hp >= S().effectiveMaxHp(target.state) && !removable(target, action).length) return false;
    if (action.targetMode === "self") return target.combatant_id === healer.combatant_id;
    if (action.targetMode === "ally") return target.combatant_id !== healer.combatant_id && target.side === healer.side;
    if (action.targetMode === "other") return target.combatant_id !== healer.combatant_id;
    return target.side === healer.side;
  }

  function selfWorthwhile(member, action) {
    return removable(member, action).length > 0 || (bloodied(member.state) && ["action", "bonus_action"].includes(action.actionCost));
  }

  function chooseTarget(healer, setup, action, turnKey = null) {
    if (action.actionCost === "reaction" || !E().available(healer.state, action.actionCost)) return null;
    if (!resourceAvailable(healer, action, turnKey)) return null;
    const allies = healer.side === "heroes" ? setup.heroes : setup.monsters;
    const legal = allies.filter((target) => targetAllowed(healer, target, action));
    const others = legal.filter((target) => target.combatant_id !== healer.combatant_id);
    const downed = others.filter((target) => target.state.current_hp === 0);
    if (downed.length) return downed.reduce((best, item) => item.state.death_save_failures > best.state.death_save_failures ? item : best);
    const hurt = others.filter((target) => bloodied(target.state));
    if (hurt.length) return hurt.reduce((best, item) => item.state.current_hp / S().effectiveMaxHp(item.state) < best.state.current_hp / S().effectiveMaxHp(best.state) ? item : best);
    const cleansable = others.filter((target) => removable(target, action).length);
    if (cleansable.length) return cleansable[0];
    const self = legal.find((target) => target.combatant_id === healer.combatant_id);
    return self && selfWorthwhile(healer, action) ? self : null;
  }

  function priority(healer, action, target) {
    const ally = target.combatant_id !== healer.combatant_id;
    const urgency = ally && target.state.current_hp === 0 ? 0 : ally ? 1 : 2;
    const cost = action.actionCost === "bonus_action" ? 0 : 1;
    return [urgency, cost, target.state.current_hp / S().effectiveMaxHp(target.state)];
  }

  function chooseAction(healer, setup, turnKey = null) {
    const choices = (healer.state.template.healingActions || []).map((action) => ({ action, target: chooseTarget(healer, setup, action, turnKey) })).filter((item) => item.target);
    choices.sort((a, b) => {
      const pa = priority(healer, a.action, a.target), pb = priority(healer, b.action, b.target);
      return pa[0] - pb[0] || pa[1] - pb[1] || pa[2] - pb[2];
    });
    return choices[0] || null;
  }

  function restore(state, amount) {
    if (state.is_dead || amount <= 0 || swarm(state)) return 0;
    const before = state.current_hp;
    state.current_hp = Math.min(S().effectiveMaxHp(state), before + amount);
    const healed = state.current_hp - before;
    if (healed > 0) {
      state.is_alive = true; state.is_unconscious = false; state.is_stable = false;
      state.death_save_successes = 0; state.death_save_failures = 0;
    }
    return healed;
  }

  function resolve(sequence, round, healer, target, action, turnKey = null) {
    if (!targetAllowed(healer, target, action) || !resourceAvailable(healer, action, turnKey)) throw new Error("Illegal healing target or turn.");
    if (slotHeal(action)) {
      if (!turnKey) throw new Error("Spell-slot healing requires an active turn key.");
      C().markSlotSpellCast(healer.state, turnKey);
    }
    E().spend(healer.state, action.actionCost);
    const rolls = Array.from({ length: action.diceCount || 0 }, () => window.IRON_PIT_DICE.roll(action.diceSize || 6));
    const total = rolls.reduce((sum, roll) => sum + roll, 0) + (action.healingBonus || 0);
    const hpBefore = target.state.current_hp, healed = restore(target.state, total);
    const removed = removable(target, action);
    removed.forEach((id) => R().removeCondition(target, id));
    let remaining = null;
    if (action.resourceId) {
      healer.state.resources[action.resourceId] -= action.resourceCost || 1;
      remaining = healer.state.resources[action.resourceId];
    }
    let description = `${healer.state.template.name} uses ${action.name} on ${target.state.template.name} and restores ${healed} HP.`;
    if (removed.length) description += ` Ends: ${removed.map((id) => id.replaceAll("_", " ").toUpperCase()).join(", ")}.`;
    return {
      sequence, round_number: round, event_type: "healing", actor_id: healer.combatant_id, actor_name: healer.state.template.name,
      target_id: target.combatant_id, target_name: target.state.template.name,
      healing_roll: { notation: rolls.length ? `${rolls.length}d${action.diceSize || 6}+${action.healingBonus || 0}` : String(action.healingBonus || 0), rolls, modifier: action.healingBonus || 0, total },
      hp_before: hpBefore, hp_after: target.state.current_hp, death_save_successes: target.state.death_save_successes,
      death_save_failures: target.state.death_save_failures, is_stable: target.state.is_stable, is_dead: target.state.is_dead,
      removed_condition_ids: removed, feature_id: action.id, resource_remaining: remaining, animation: action.animation || "healing",
      description,
    };
  }

  window.IRON_PIT_BROWSER_HEALING = { bloodied, chooseAction, chooseTarget, resolve, restore };
})();
