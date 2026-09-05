"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = globalThis;
const load = (name) => vm.runInThisContext(fs.readFileSync(path.join(__dirname, name), "utf8"), { filename: name });
for (const file of [
  "browser-heroes.js", "browser-condition-immunity.js", "browser-condition-rules.js", "browser-action-economy.js",
  "browser-grapple.js", "browser-modifiers.js", "browser-state.js", "browser-rage.js", "browser-rolls.js",
  "browser-undead-fortitude.js", "browser-zero-hp.js", "browser-attack.js", "browser-spellcasting.js",
  "browser-spell-modifiers.js", "browser-spell-attack.js",
]) load(file);

const S = window.IRON_PIT_BROWSER_STATE;
const X = window.IRON_PIT_BROWSER_SPELL_ATTACK;
const A = window.IRON_PIT_BROWSER_ATTACK;
const M = window.IRON_PIT_BROWSER_MODIFIERS;
const base = window.IRON_PIT_BROWSER_HEROES["karnok-stoneward-l1"];
const guidingBolt = {
  id: "guiding-bolt", name: "Guiding Bolt", level: 1, actionCost: "action", range: 120,
  attackBonus: 5, damageDiceCount: 4, damageDiceSize: 6, damageBonus: 0, damageType: "radiant",
  onHitModifierEffects: [{
    kind: "attacks-against-advantage", flatBonus: 0, diceCount: 0, diceSize: 0, damageType: null,
    consumeOnAttackAgainst: true, expiresAfterSourceTurns: 1,
  }], animation: "guiding-bolt",
};
const rayOfFrost = {
  id: "ray-of-frost", name: "Ray of Frost", level: 0, actionCost: "action", range: 60,
  attackBonus: 5, damageDiceCount: 1, damageDiceSize: 8, damageBonus: 0, damageType: "cold",
  onHitModifierEffects: [{ kind: "speed", flatBonus: -10, expiresAtEndOfTargetTurn: true }],
  animation: "ray-of-frost",
};

function dice(values) {
  const rolls = [...values];
  window.IRON_PIT_DICE = {
    roll: (sides) => {
      if (!rolls.length) throw new Error("fixed dice exhausted");
      const value = rolls.shift();
      if (value < 1 || value > sides) throw new Error(`invalid d${sides}: ${value}`);
      return value;
    },
    rollMany: (count, sides) => Array.from({ length: count }, () => window.IRON_PIT_DICE.roll(sides)),
  };
}

function member(id, side, position, options = {}) {
  const template = structuredClone(base);
  template.id = `template-${id}`; template.name = id; template.armor_class = options.armorClass ?? 10;
  template.resources = options.caster ? { "spell-slot-1": 1 } : {};
  return { combatant_id: id, side, position_ft: position, state: S.buildState(template) };
}

function setup(targetAc = 10) {
  const caster = member("caster", "heroes", 0, { caster: true });
  const ally = member("ally", "heroes", 5);
  const target = member("target", "monsters", 30, { armorClass: targetAc });
  return { caster, ally, target, arena: { heroes: [caster, ally], monsters: [target] } };
}

{
  const { caster, ally, target, arena } = setup();
  dice([15, 6, 5, 4, 3]);
  const event = X.resolve(1, 1, caster, target, guidingBolt, arena, "1:caster");
  assert.equal(event.hit, true);
  assert.equal(event.critical, false);
  assert.equal(event.damage_roll.total, 18);
  assert.equal(event.damage_components[0].damage_type, "radiant");
  assert.equal(caster.state.resources["spell-slot-1"], 0);
  assert.equal(caster.state.action_available, false);
  assert.equal(target.state.active_modifiers.length, 1);
  assert.equal(target.state.active_modifiers[0].consume_on_attack_against, true);
  assert.equal(target.state.active_modifiers[0].expires_source_turn_end_round, 2);

  target.state.template.armor_class = 30;
  const attack = ally.state.template.attacks.find((item) => item.id === ally.state.template.primary_attack_id);
  dice([5, 15]);
  const followup = A.resolveAttack(2, 1, ally, target, attack, 5, { spendAction: false });
  assert.equal(followup.attack_roll.mode, "advantage");
  assert.equal(target.state.active_modifiers.length, 0);
}

{
  const { caster, target, arena } = setup();
  dice([15, 6]);
  const event = X.resolve(1, 1, caster, target, rayOfFrost, arena, "1:caster");
  assert.equal(event.hit, true);
  assert.equal(target.state.active_modifiers.length, 1);
  assert.equal(target.state.active_modifiers[0].flat_bonus, -10);
  assert.equal(target.state.active_modifiers[0].expires_at_end_of_target_turn, true);
  assert.equal(M.effectiveSpeed(target.state), target.state.template.speed_ft - 10);
  M.expireTargetTurn(target.state);
  assert.equal(M.effectiveSpeed(target.state), target.state.template.speed_ft);
}

{
  const { caster, target, arena } = setup(30);
  dice([10]);
  const event = X.resolve(1, 1, caster, target, guidingBolt, arena, "1:caster");
  assert.equal(event.hit, false);
  assert.equal(event.damage_roll, null);
  assert.equal(target.state.active_modifiers.length, 0);
  assert.equal(caster.state.resources["spell-slot-1"], 0);
}

{
  const { caster, target, arena } = setup(30);
  target.position_ft = 5;
  dice([18, 2]);
  const event = X.resolve(1, 1, caster, target, guidingBolt, arena, "1:caster");
  assert.equal(event.attack_roll.mode, "disadvantage");
  assert.equal(event.attack_roll.selected_roll, 2);
}

{
  const { caster, target, arena } = setup();
  caster.state.resources = { "spell-slot-2": 1 };
  dice([20]);
  assert.throws(() => X.resolve(1, 1, caster, target, guidingBolt, arena, "1:caster"), /No level 1 spell slot/);
  assert.equal(caster.state.resources["spell-slot-2"], 1);
  assert.equal(caster.state.action_available, true);
}

console.log("Browser Guiding Bolt and Ray of Frost spell-attack regressions passed.");
require("./browser-spell-attack-context.test.cjs");
