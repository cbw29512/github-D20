"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = globalThis;
window.IRON_PIT_BROWSER_STATE = { sizeAtMost: () => true };
window.IRON_PIT_BROWSER_FORMATION = {
  targetOrder: (actor, setup) => actor.side === "monsters" ? setup.heroes : setup.monsters,
  saveDistance: (actor, target, range) => Math.min(Math.abs(actor.position_ft - target.position_ft), range),
};
vm.runInThisContext(fs.readFileSync(path.join(__dirname, "browser-saves.js"), "utf8"), { filename: "browser-saves.js" });

const member = (side, index, position) => ({
  combatant_id: `${side}-${index}`, side, position_ft: position,
  state: { is_alive: true, is_dead: false, current_hp: 10 },
});
const monsters = [member("monsters", 0, 15), member("monsters", 1, 15), member("monsters", 2, 15)];
const heroes = Array.from({ length: 6 }, (_, index) => member("heroes", index, 5));
const setup = { heroes, monsters };
const line = { name: "Acid Breath", range: 30, area: { shape: "line", sizeFt: 30, widthFt: 5 } };

assert.deepEqual(
  window.IRON_PIT_BROWSER_SAVES.targetsFor(monsters[1], setup, line).map((target) => target.combatant_id),
  ["heroes-1", "heroes-4"],
);
heroes[1].state.current_hp = 0; heroes[1].state.is_alive = false; heroes[1].state.is_dead = true;
heroes[4].state.current_hp = 0; heroes[4].state.is_alive = false; heroes[4].state.is_dead = true;
assert.deepEqual(window.IRON_PIT_BROWSER_SAVES.targetsFor(monsters[1], setup, line), []);

console.log("Browser 3x2 Line targeting regression passed.");
