(() => {
  "use strict";

  const A = () => window.IRON_PIT_BROWSER_ATTACK;
  const C = () => window.IRON_PIT_BROWSER_CHARGE;
  const D = () => window.IRON_PIT_DICE;
  const F = () => window.IRON_PIT_BROWSER_FORMATION;
  const R = () => window.IRON_PIT_BROWSER_LIGHT_ATTACK;
  const V = () => window.IRON_PIT_BROWSER_SAVES;
  const X = () => window.IRON_PIT_BROWSER_RESOURCES || { spend: () => {} };
  const WM = () => window.IRON_PIT_BROWSER_WEAPON_MASTERY || { resolveCleave: (sequence) => ({ events: [], sequence }) };
  const E = () => window.IRON_PIT_ACTION_ECONOMY || { available: (s) => s.action_available, spend: (s) => { s.action_available = false; } };
  const slotData = (slot) => Array.isArray(slot) ? { attackIds: slot, saveActionIds: [] }
    : { attackIds: slot.attackIds || [], saveActionIds: slot.saveActionIds || [] };

  function saveChoice(member, setup, data) {
    const allowed = new Set(data.saveActionIds);
    for (const target of F().targetOrder(member, setup)) {
      const action = (member.state.template.saving_throw_actions || []).find((item) => {
        const distance = F().saveDistance(member, target, item.range);
        return allowed.has(item.id) && V().resourceAvailable(member.state, item) && V().legalAction(item, target, distance);
      });
      if (action) return { target, save: action, distance: F().saveDistance(member, target, action.range) };
    }
    return null;
  }
  function attackChoice(member, setup, data, rangedBackline = false) {
    if (rangedBackline) {
      const ranged = F().chooseAttack(member, setup, data.attackIds, "ranged", true);
      if (ranged) return ranged;
    }
    if (F().isBackline(member) && F().alliedFrontlineActive(member, setup)) {
      const ranged = F().chooseAttack(member, setup, data.attackIds, "ranged");
      if (ranged) return ranged;
    }
    return F().chooseAttack(member, setup, data.attackIds, "melee")
      || F().chooseAttack(member, setup, data.attackIds, "ranged");
  }
  function useRangedSplit(member, setup, slots) {
    if (F().isBackline(member)) return false;
    if (!F().hasFrontlineTarget(member, setup) || !F().hasBacklineTarget(member, setup)) return false;
    if (!slots.slice(1).some((slot) => F().flexibleSlotHasBoth(member, slotData(slot).attackIds))) return false;
    return D().roll(100) >= 76;
  }

  function resolveAttackAction(sequence, round, member, setup) {
    const definition = member.state.template.attack_action, slots = definition?.slots;
    if (!slots?.length || !E().available(member.state, "action") || !F().targetOrder(member, setup).length) {
      return { events: [], sequence };
    }
    const events = [];
    E().spend(member.state, "action");
    let openingFeature = C()?.openingFeature?.(round, member, setup) || null;
    let lightTrigger = null, rangedSplitUsed = false;
    const rangedSplit = useRangedSplit(member, setup, slots);
    const turnKey = `${round}:${member.combatant_id}`;

    slots.forEach((slot, index) => {
      if (member.state.is_dead || member.state.is_unconscious) return;
      const data = slotData(slot);
      const splitThis = index > 0 && rangedSplit && !rangedSplitUsed && F().flexibleSlotHasBoth(member, data.attackIds);
      const choice = attackChoice(member, setup, data, splitThis);
      if (choice) {
        if (choice.attack.resourceId) X().spend(member.state, choice.attack.resourceId, choice.attack.resourceCost || 1);
        if (splitThis && choice.attack.kind === "ranged") rangedSplitUsed = true;
        const pack = window.IRON_PIT_BROWSER_STATE.packTactics(member, setup);
        const featureId = openingFeature || (pack ? "pack-tactics" : definition.id);
        const event = A().resolveAttack(sequence++, round, member, choice.target, choice.attack, choice.distance, {
          spendAction: false, advantage: pack ? 1 : 0, setup, featureId, turnKey,
          allowReckless: true, ignoreCloseThreat: true,
        });
        events.push(event);
        const cleave = WM().resolveCleave(sequence, round, member, event, choice.attack, setup, turnKey);
        events.push(...cleave.events); sequence = cleave.sequence;
        if (definition.isAttackAction && !lightTrigger && choice.attack.light) lightTrigger = choice.attack;
        openingFeature = null;
        return;
      }
      const saved = saveChoice(member, setup, data);
      if (saved) {
        events.push(V().resolveAction(sequence++, round, member, saved.target, saved.save, saved.distance, { spendAction: false }));
      }
    });

    if (definition.isAttackAction && lightTrigger) {
      const extra = R().resolve(sequence, round, member, setup, lightTrigger, turnKey);
      events.push(...extra.events); sequence = extra.sequence;
    }
    return { events, sequence };
  }

  window.IRON_PIT_BROWSER_MULTIATTACK = { resolveAttackAction };
})();
