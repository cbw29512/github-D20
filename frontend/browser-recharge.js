(() => {
  "use strict";

  const R = () => window.IRON_PIT_BROWSER_RESOURCES;
  const D = () => window.IRON_PIT_DICE;

  function resolve(sequence, round, member) {
    const rules = member.state.template.resource_recharges || {};
    const events = [];
    for (const [resourceId, rule] of Object.entries(rules)) {
      if (R().uses(member.state, resourceId) >= R().maximum(member.state, resourceId)) continue;
      const dieSize = Number(rule.dieSize || 6), minimum = Number(rule.minimum), maximum = Number(rule.maximum || dieSize);
      if (!Number.isInteger(dieSize) || dieSize < 2 || minimum < 1 || minimum > maximum || maximum > dieSize) {
        throw new Error(`Invalid Recharge rule for ${resourceId}.`);
      }
      const roll = D().roll(dieSize), recharged = roll >= minimum && roll <= maximum;
      if (recharged) R().restore(member.state, resourceId);
      const name = rule.name || resourceId;
      events.push({
        sequence: sequence++, round_number: round, event_type: "feature",
        actor_id: member.combatant_id, actor_name: member.state.template.name,
        feature_id: resourceId, resource_remaining: R().uses(member.state, resourceId), animation: "recharge",
        description: `${member.state.template.name} rolls ${roll} for ${name} Recharge and ${recharged ? "recharges" : "does not recharge"}.`,
      });
    }
    return { events, sequence };
  }

  window.IRON_PIT_BROWSER_RECHARGE = { resolve };
})();
