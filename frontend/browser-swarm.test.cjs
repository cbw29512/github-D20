"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = globalThis;
const load = (name) => vm.runInThisContext(fs.readFileSync(path.join(__dirname, name), "utf8"), { filename: name });
load("browser-state.js");
load("browser-zero-hp.js");
load("browser-healing.js");
load("browser-precombat-spells.js");

const template = {
  id: "test-swarm", name: "Test Swarm", kind: "monster", max_hp: 10, speed_ft: 20,
  traits: ["swarm"], resources: {}, defensive_spell_actions: [],
};
const state = window.IRON_PIT_BROWSER_STATE.buildState(template);
state.current_hp = 3;
assert.equal(window.IRON_PIT_BROWSER_HEALING.restore(state, 7), 0);
assert.equal(state.current_hp, 3);
assert.equal(window.IRON_PIT_BROWSER_STATE.grantTemporaryHp(state, 9), 0);
assert.equal(state.temporary_hp, 0);

const member = {
  combatant_id: "monster-1:test-swarm", side: "monsters", position_ft: 0,
  state: window.IRON_PIT_BROWSER_STATE.buildState({
    ...template,
    resources: { "spell-slot-1": 1 },
    defensive_spell_actions: [{
      id: "false-life", name: "False Life", level: 1, concentration: false,
      targetPolicy: "self", targetCount: 1,
      temporaryHp: 5, temporaryHpPerSlotAbove: 0, damageResistances: [], modifierEffects: [], priority: 1,
    }],
  }),
};
const spell = member.state.template.defensive_spell_actions[0];
const event = window.IRON_PIT_BROWSER_PRECOMBAT_SPELLS.resolve(
  1, member, [member], spell, 1,
);
assert.equal(member.state.temporary_hp, 0);
assert.equal(member.state.resources["spell-slot-1"], 0);
assert.ok(!event.description.includes("Temporary HP"));

console.log("Browser Swarm trait blocks Hit Point recovery and Temporary HP.");
