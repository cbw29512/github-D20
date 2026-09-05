(() => {
  "use strict";

  const E = () => window.IRON_PIT_ACTION_ECONOMY;
  const P = () => window.IRON_PIT_BROWSER_SPELLCASTING;
  const PRIORITY = {
    paralyzed: 0, stunned: 0, incapacitated: 0, petrified: 0,
    blinded: 1, restrained: 1, poisoned: 2, frightened: 2, charmed: 2,
    deafened: 3, grappled: 3, prone: 4, exhaustion: 4,
  };

  const distance = (a, b) => Math.abs(a.position_ft - b.position_ft);
  const allies = (member, setup) => member.side === "heroes" ? setup.heroes : setup.monsters;

  function targetAllowed(remover, target, action) {
    if (!target.state.is_alive || target.state.is_dead || target.side !== remover.side) return false;
    if (distance(remover, target) > action.range) return false;
    if (action.targetMode === "self") return target.combatant_id === remover.combatant_id;
    if (action.targetMode === "ally") return target.combatant_id !== remover.combatant_id;
    return true;
  }

  function costs(action, count) {
    const result = { ...(action.resourceCosts || {}) };
    Object.entries(action.resourceCostsPerCondition || {}).forEach(([id, cost]) => {
      result[id] = (result[id] || 0) + cost * count;
    });
    return result;
  }

  function resourcesAvailable(member, action, count) {
    return Object.entries(costs(action, count)).every(([id, cost]) => (member.state.resources[id] || 0) >= cost);
  }

  function effectAllows(target, conditionId, actionId) {
    return target.state.timed_effects.filter((effect) => effect.effect_id === conditionId).every((effect) =>
      !effect.allowed_removal_action_ids?.length || effect.allowed_removal_action_ids.includes(actionId),
    );
  }

  function removable(target, action) {
    const allowed = new Set(action.removableConditions || []);
    return target.state.active_effect_ids
      .filter((id) => allowed.has(id) && effectAllows(target, id, action.id))
      .sort((a, b) => (PRIORITY[a] ?? 9) - (PRIORITY[b] ?? 9) || a.localeCompare(b));
  }

  function affordable(member, target, action) {
    const result = removable(target, action).slice(0, action.maxConditionsPerUse || 1);
    while (result.length && !resourcesAvailable(member, action, result.length)) result.pop();
    return result;
  }

  function slotAvailable(remover, action, turnKey) {
    return !action.expendsSpellSlot || P().slotSpellAvailable(remover.state, turnKey);
  }

  function chooseAction(remover, setup, turnKey) {
    const choices = [];
    for (const action of remover.state.template.condition_removal_actions || []) {
      if (action.actionCost === "reaction" || !E().available(remover.state, action.actionCost)) continue;
      if (!slotAvailable(remover, action, turnKey)) continue;
      for (const target of allies(remover, setup)) {
        if (!targetAllowed(remover, target, action)) continue;
        const conditions = affordable(remover, target, action);
        if (conditions.length) choices.push({ action, target, conditions });
      }
    }
    choices.sort((a, b) => {
      const urgency = (PRIORITY[a.conditions[0]] ?? 9) - (PRIORITY[b.conditions[0]] ?? 9);
      if (urgency) return urgency;
      const economy = (a.action.actionCost === "bonus_action" ? 0 : 1) - (b.action.actionCost === "bonus_action" ? 0 : 1);
      if (economy) return economy;
      if (a.conditions.length !== b.conditions.length) return b.conditions.length - a.conditions.length;
      return distance(remover, a.target) - distance(remover, b.target);
    });
    return choices[0] || null;
  }

  function removeCondition(target, id) {
    target.state.active_effect_ids = target.state.active_effect_ids.filter((item) => item !== id);
    target.state.timed_effects = target.state.timed_effects.filter((item) => item.effect_id !== id);
    if (id === "grappled") target.state.grapple_sources = [];
  }

  function resolve(sequence, round, remover, target, action, conditionIds, turnKey) {
    if (action.actionCost === "reaction") throw new Error("Reaction cleansing requires a matching trigger.");
    if (!targetAllowed(remover, target, action) || !conditionIds?.length) throw new Error("Illegal condition-removal target.");
    if (!slotAvailable(remover, action, turnKey)) throw new Error("A spell slot was already expended to cast a spell this turn.");
    const legal = new Set(affordable(remover, target, action));
    if (conditionIds.some((id) => !legal.has(id))) throw new Error("Condition-removal action cannot remove this effect.");
    E().spend(remover.state, action.actionCost);
    if (action.expendsSpellSlot) P().markSlotSpellCast(remover.state, turnKey);
    Object.entries(costs(action, conditionIds.length)).forEach(([id, cost]) => {
      if ((remover.state.resources[id] || 0) < cost) throw new Error(`Required resource ${id} is unavailable.`);
      remover.state.resources[id] -= cost;
    });
    conditionIds.forEach((id) => removeCondition(target, id));
    const names = conditionIds.map((id) => id.replaceAll("_", " ").toUpperCase()).join(", ");
    return {
      sequence, round_number: round, event_type: "feature",
      actor_id: remover.combatant_id, actor_name: remover.state.template.name,
      target_id: target.combatant_id, target_name: target.state.template.name,
      removed_condition_ids: [...conditionIds], feature_id: action.id,
      animation: action.animation || "condition-removal",
      description: `${remover.state.template.name} uses ${action.name} on ${target.state.template.name}; ${names} ends.`,
    };
  }

  function chooseReaction(remover, setup, trigger, affectedTarget, turnKey) {
    if (!E().available(remover.state, "reaction")) return null;
    const actions = (remover.state.template.condition_removal_actions || []).filter((action) =>
      action.actionCost === "reaction" && action.reactionTrigger === trigger && slotAvailable(remover, action, turnKey),
    );
    for (const action of actions) {
      if (!targetAllowed(remover, affectedTarget, action)) continue;
      const conditions = affordable(remover, affectedTarget, action);
      if (conditions.length) return { action, target: affectedTarget, conditions };
    }
    return null;
  }

  window.IRON_PIT_BROWSER_CONDITION_REMOVAL = { chooseAction, chooseReaction, removeCondition, resolve };
})();
