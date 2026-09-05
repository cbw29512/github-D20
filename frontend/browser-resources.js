(() => {
  "use strict";

  function uses(state, resourceId) {
    return Number(state.resources?.[resourceId] || 0);
  }

  function maximum(state, resourceId) {
    return Number(state.template.resources?.[resourceId] || 0);
  }

  function available(state, resourceId, amount = 1) {
    if (!resourceId) return true;
    if (!Number.isInteger(amount) || amount <= 0) throw new Error("Resource cost must be a positive integer.");
    return uses(state, resourceId) >= amount;
  }

  function spend(state, resourceId, amount = 1) {
    if (!resourceId) return null;
    if (!available(state, resourceId, amount)) throw new Error(`Resource ${resourceId} has insufficient uses.`);
    state.resources[resourceId] -= amount;
    return state.resources[resourceId];
  }

  function restore(state, resourceId, amount = null) {
    if (!resourceId) throw new Error("Resource ID is required.");
    const max = maximum(state, resourceId);
    if (!max) throw new Error(`Resource ${resourceId} is missing from the template.`);
    if (amount != null && (!Number.isInteger(amount) || amount <= 0)) throw new Error("Resource restore must be positive.");
    state.resources[resourceId] = amount == null ? max : Math.min(max, uses(state, resourceId) + amount);
    return state.resources[resourceId];
  }

  window.IRON_PIT_BROWSER_RESOURCES = { available, maximum, restore, spend, uses };
})();
