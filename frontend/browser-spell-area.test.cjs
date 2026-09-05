"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = globalThis;
const load = (name) => vm.runInThisContext(fs.readFileSync(path.join(__dirname, name), "utf8"), { filename: name });
load("browser-spell-area.js");
const A = window.IRON_PIT_BROWSER_SPELL_AREA;

const member = (side, index, position) => ({
  combatant_id: `${side}-${index}`, side, position_ft: position,
  state: { is_alive: true, is_dead: false, current_hp: 10 },
});
const setup = (heroes, monsters) => ({ heroes, monsters });

assert.equal(A.areaSlotCount(5), 1);
assert.equal(A.areaSlotCount(10), 2);
assert.equal(A.areaSlotCount(20), 4);
assert.equal(A.areaSlotCount(30), 6);
assert.equal(A.areaSlotCount(60), 6);

{
  const heroes = [member("heroes", 0, 0)];
  const monsters = Array.from({ length: 6 }, (_, i) => member("monsters", i, 30));
  const result = A.bestPlacement(heroes[0], setup(heroes, monsters), 20, 150);
  assert.equal(result.enemyIds.length, 4);
  assert.equal(result.friendlyIds.length, 0);
}

{
  const heroes = [member("heroes", 0, 0)];
  const monsters = Array.from({ length: 6 }, (_, i) => member("monsters", i, 60));
  assert.equal(A.bestPlacement(heroes[0], setup(heroes, monsters), 30, 150).enemyIds.length, 6);
}

{
  const heroes = [member("heroes", 0, 0)];
  const monsters = Array.from({ length: 3 }, (_, i) => member("monsters", i, 5));
  const result = A.bestPlacement(heroes[0], setup(heroes, monsters), 20, 150);
  assert.equal(result.enemyIds.length, 3);
  assert.equal(result.friendlyIds.length, 0);
  assert.ok(result.centerFt > 5);
}

{
  const heroes = [member("heroes", 0, 0), member("heroes", 1, 0)];
  const monsters = [member("monsters", 0, 5), member("monsters", 1, 5)];
  assert.equal(A.bestPlacement(heroes[0], setup(heroes, monsters), 10, 5), null);
  const protectedResult = A.bestPlacement(heroes[0], setup(heroes, monsters), 10, 5, ["heroes-0", "heroes-1"]);
  assert.equal(protectedResult.enemyIds.length, 2);
  assert.equal(protectedResult.friendlyIds.length, 0);
  assert.deepEqual(protectedResult.protectedFriendlyIds, ["heroes-0", "heroes-1"]);
}

{
  const heroes = [member("heroes", 0, 0), member("heroes", 1, 5)];
  const monsters = [
    ...Array.from({ length: 3 }, (_, i) => member("monsters", i, 10)),
    ...Array.from({ length: 3 }, (_, i) => member("monsters", i + 3, 15)),
  ];
  const result = A.bestPlacement(heroes[0], setup(heroes, monsters), 40, 5280);
  assert.equal(result.enemyIds.length, 6);
  assert.equal(result.friendlyIds.length, 0);
  assert.ok(result.centerFt >= 50);
}

{
  const heroes = [member("heroes", 0, 0)];
  const monsters = Array.from({ length: 3 }, (_, i) => member("monsters", i, 30));
  monsters[1].state.current_hp = 0;
  monsters[1].state.is_alive = false;
  monsters[1].state.is_dead = true;
  assert.equal(A.bestPlacement(heroes[0], setup(heroes, monsters), 10, 150).enemyIds.length, 1);
}

const queueDice = (values) => {
  const queue = [...values];
  const roll = (sides) => { const value = queue.shift(); assert.ok(value && value <= sides); return value; };
  return { roll, rollMany: (count, sides) => Array.from({ length: count }, () => roll(sides)) };
};
window.IRON_PIT_BROWSER_ROLLS = {
  modeFromSources: () => "normal",
  d20: (bonus) => { const natural = window.IRON_PIT_DICE.roll(20); return { rolls: [natural], selected_roll: natural, modifier: bonus, mode: "normal", total: natural + bonus }; },
};
window.IRON_PIT_BROWSER_MODIFIERS = { applyD20Bonus: (_state, _kind, roll) => roll };
window.IRON_PIT_BROWSER_CONDITION_RULES = { autoFailStrDex: () => false };
window.IRON_PIT_BROWSER_STATE = { sizeAtMost: () => true, beginTurn: (state) => { state.action_available = true; state.bonus_action_available = true; }, packTactics: () => false };
window.IRON_PIT_BROWSER_RESOURCES = {
  available: (state, id, cost) => (state.resources[id] || 0) >= cost,
  spend: (state, id, cost) => { state.resources[id] -= cost; }, uses: (state, id) => state.resources[id] || 0,
};
window.IRON_PIT_ACTION_ECONOMY = {
  available: (state, cost) => cost === "action" ? state.action_available : state.bonus_action_available,
  spend: (state, cost) => { if (cost === "action") state.action_available = false; else state.bonus_action_available = false; },
};
window.IRON_PIT_BROWSER_ATTACK = { adjustedDamage: (_state, damage) => damage, applyDamage: (state, damage) => { state.current_hp = Math.max(0, state.current_hp - damage); return null; } };
window.IRON_PIT_BROWSER_GRAPPLE = { apply: () => [], cleanup: () => {}, shouldEscape: () => false };
window.IRON_PIT_BROWSER_CONCENTRATION = { endIfIncapacitated: () => {} };
window.IRON_PIT_BROWSER_FORMATION = {
  targetOrder: (actor, arena) => actor.side === "monsters" ? arena.heroes : arena.monsters,
  saveDistance: (actor, target, range) => Math.min(Math.abs(actor.position_ft - target.position_ft), range), chooseStandardAttack: () => null,
};
load("browser-saves.js");

const breath = { id: "test-breath", name: "Test Breath", saveAbility: "constitution", dc: 11, range: 15,
  area: { shape: "cone", sizeFt: 15 }, damageDiceCount: 6, damageDiceSize: 6, damageBonus: 0,
  damageType: "poison", successDamage: "half", resourceId: "test-breath", resourceCost: 1 };
const saveTarget = (id) => ({ combatant_id: id, side: "heroes", position_ft: 5, state: {
  template: { name: id, saving_throw_bonuses: { constitution: 0 } }, active_effect_ids: [], current_hp: 40, temporary_hp: 0,
  death_save_successes: 0, death_save_failures: 0, is_alive: true, is_dead: false, is_unconscious: false, is_stable: false, concentration: null,
} });
const breathActor = { combatant_id: "monster:dragon", side: "monsters", position_ft: 10, state: {
  template: { name: "Test Dragon", saving_throw_actions: [breath], attack_action: { id: "multi" } }, resources: { "test-breath": 1 },
  action_available: true, bonus_action_available: true, active_effect_ids: [], is_alive: true, is_dead: false, is_unconscious: false,
} };
const breathSetup = { heroes: [saveTarget("hero:1"), saveTarget("hero:2"), saveTarget("hero:3")], monsters: [breathActor] };
window.IRON_PIT_DICE = queueDice([1, 1, 2, 3, 4, 5, 6, 1, 1]);
const area = window.IRON_PIT_BROWSER_SAVES.resolveTurnAction(1, 1, breathActor, breathSetup, true);
assert.equal(area.events.length, 3);
assert.deepEqual(area.events.map((event) => event.damage_roll.rolls), Array(3).fill([1, 2, 3, 4, 5, 6]));
assert.equal(breathActor.state.resources["test-breath"], 0);

breathActor.state.resources["test-breath"] = 1;
window.IRON_PIT_BROWSER_CHARGE = { resolveClosing: () => null };
window.IRON_PIT_BROWSER_MULTIATTACK = { resolveAttackAction: () => { throw new Error("Multiattack ran before Recharge save"); } };
window.IRON_PIT_BROWSER_RAGE = { enter: () => null, finalize: () => null };
window.IRON_PIT_BROWSER_ACTION_SURGE = { resolveAttack: () => null };
window.IRON_PIT_BROWSER_SUPPORT = { resolve: () => null, secondWind: () => null, adrenaline: () => null };
window.IRON_PIT_BROWSER_TACTICAL_SHIFT = { resolve: () => null };
window.IRON_PIT_BROWSER_ONGOING_SPELL_CONTROL = { forcedRetreatActive: () => false };
window.IRON_PIT_BROWSER_SPELL_OFFENSE = { resolve: () => null };
window.IRON_PIT_BROWSER_STANDARD_ATTACK_ACTION = { resolve: () => { throw new Error("standard attack unexpectedly ran"); } };
load("browser-turn.js");
window.IRON_PIT_DICE = queueDice([1, 1, 2, 3, 4, 5, 6, 1, 1]);
const turn = window.IRON_PIT_BROWSER_TURN.resolveTurn(20, 2, breathActor, breathSetup);
assert.equal(turn.events.filter((event) => event.feature_id === "test-breath").length, 3);
assert.equal(breathActor.state.resources["test-breath"], 0);

console.log("Browser spell-area and Recharge-area regressions passed.");
