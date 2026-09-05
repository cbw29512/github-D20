"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = globalThis;

const load = (name) => vm.runInThisContext(fs.readFileSync(path.join(__dirname, name), "utf8"), { filename: name });
for (const file of [
  "browser-heroes.js", "browser-monsters.js", "browser-monsters-fixed.js",
  "browser-condition-immunity.js", "browser-condition-rules.js", "browser-action-economy.js",
  "browser-grapple.js", "browser-timed-conditions.js", "browser-state.js", "browser-resources.js", "browser-recharge.js", "browser-rage.js", "browser-rolls.js",
  "browser-zero-hp.js", "browser-weapon-mastery.js", "browser-graze.js", "browser-vex.js", "browser-attack.js",
  "browser-reactions.js", "browser-reaction-movement.js", "browser-saves.js", "browser-condition-lifecycle.js",
  "browser-charge.js", "browser-light-weapons.js", "browser-light-attack.js", "browser-standard-attack-action.js",
  "browser-multiattack.js", "browser-healing.js", "browser-spellcasting.js", "browser-condition-removal.js",
  "browser-support.js", "browser-turn.js", "browser-formation.js", "browser-engine.js",
]) load(file);

function deterministicDice(seed = 12345) {
  let state = seed >>> 0;
  const roll = (sides) => {
    state = (1664525 * state + 1013904223) >>> 0;
    return (state % sides) + 1;
  };
  return { roll, rollMany: (count, sides) => Array.from({ length: count }, () => roll(sides)) };
}

function queuedDice(values, fallback = 10) {
  const queue = [...values];
  const roll = (sides) => {
    const raw = queue.length ? queue.shift() : fallback;
    return ((raw - 1) % sides) + 1;
  };
  return { roll, rollMany: (count, sides) => Array.from({ length: count }, () => roll(sides)) };
}

function fight(heroIds, monsterIds, dice = deterministicDice()) {
  window.IRON_PIT_DICE = dice;
  return window.IRON_PIT_BROWSER_ENGINE.runEncounter({ hero_ids: heroIds, monster_ids: monsterIds });
}

{
  const battle = fight(["karnok-stoneward-l1"], ["srd-commoner"]);
  assert.notEqual(battle.outcome, "active");
  assert.ok(battle.events.some((event) => event.event_type === "attack"));
  assert.equal(battle.setup.heroes[0].position_ft, 5);
  assert.equal(battle.setup.monsters[0].position_ft, 10);
  assert.equal(Object.hasOwn(battle.setup, "starting_distance_ft"), false, "formation setup must not expose a user-configurable starting distance");
  assert.equal(Math.abs(battle.setup.heroes[0].position_ft - battle.setup.monsters[0].position_ft), 5, "front-line melee must begin engaged");
}

{
  const source = window.IRON_PIT_BROWSER_HEROES["karnok-stoneward-l1"];
  const originalAc = source.armor_class;
  const originalAttackName = source.attacks[0].name;
  const first = window.IRON_PIT_BROWSER_STATE.buildState(source);
  first.current_hp = 1;
  first.template.armor_class += 10;
  first.template.attacks[0].name = "runtime-only";
  const second = window.IRON_PIT_BROWSER_STATE.buildState(source);
  assert.notEqual(first.template, source, "fight state must not retain the source card object");
  assert.equal(source.armor_class, originalAc, "runtime AC changes must not mutate the source card");
  assert.equal(source.attacks[0].name, originalAttackName, "nested runtime changes must not mutate the source card");
  assert.equal(second.current_hp, source.max_hp, "a new fight must start from source HP");
  assert.equal(second.template.armor_class, originalAc, "a new fight must not inherit prior runtime modifiers");
}

{
  const batTemplate = structuredClone(window.IRON_PIT_BROWSER_MONSTERS["srd-bat"]);
  const heroTemplate = structuredClone(window.IRON_PIT_BROWSER_HEROES["karnok-stoneward-l1"]);
  const bat = { combatant_id: "monster-1:bat", side: "monsters", position_ft: 5, state: window.IRON_PIT_BROWSER_STATE.buildState(batTemplate) };
  const hero = { combatant_id: "hero-1:karnok", side: "heroes", position_ft: 0, state: window.IRON_PIT_BROWSER_STATE.buildState(heroTemplate) };
  window.IRON_PIT_BROWSER_STATE.beginTurn(bat.state);
  window.IRON_PIT_DICE = queuedDice([20]);
  const event = window.IRON_PIT_BROWSER_ATTACK.resolveAttack(1, 1, bat, hero, batTemplate.attacks[0], 5);
  assert.equal(event.critical, true);
  assert.equal(event.damage_roll.notation, "1");
  assert.deepEqual(event.damage_roll.rolls, []);
  assert.equal(event.damage_roll.total, 1, "fixed damage must not double on a critical hit");
}

{
  const battle = fight(["karnok-stoneward-l1"], ["srd-bandit"], deterministicDice(7));
  const karnokAttacks = battle.events.filter((event) => event.event_type === "attack" && event.actor_id.startsWith("hero-1:"));
  assert.equal(karnokAttacks[0].weapon_id, "karnok-greatsword", "front-line melee starts engaged");
  assert.equal(karnokAttacks.filter((event) => event.weapon_id === "karnok-shortbow").length, 0);
}

{
  const battle = fight(["karnok-stoneward-l1"], ["srd-dire-wolf", "srd-dire-wolf"], queuedDice([1, 20, 20, 20, 10, 10, 10]));
  const packAttack = battle.events.find((event) => event.event_type === "attack" && event.feature_id === "pack-tactics");
  assert.ok(packAttack, "expected Pack Tactics attack");
  assert.equal(packAttack.attack_roll.mode, "advantage");
}

{
  const battle = fight(["karnok-stoneward-l1"], ["srd-dire-wolf"],
    queuedDice([20, 1, 20, 1, 1, 1, 1, 1, 1, 1, 1, 10, 1]));
  assert.ok(battle.events.some((event) => event.event_type === "attack" && event.critical), "expected a critical attack");
  assert.ok(battle.events.some((event) => event.event_type === "attack" && event.attack_roll.selected_roll === 1), "expected a natural 1 attack");
}

{
  const battle = fight(["karnok-stoneward-l1"], ["srd-wolf", "srd-wolf"],
    queuedDice([1, 20, 20, 20, 6, 6, 10, 10]));
  assert.ok(battle.events.some((event) => event.applied_condition_ids?.includes("prone")), "expected Wolf/Dire Wolf Prone support");
}

{
  const heroTemplate = structuredClone(window.IRON_PIT_BROWSER_HEROES["karnok-stoneward-l1"]);
  const axeTemplate = structuredClone(window.IRON_PIT_BROWSER_MONSTERS["srd-axe-beak"]);
  const hero = { combatant_id: "hero-1:karnok", side: "heroes", position_ft: 0, state: window.IRON_PIT_BROWSER_STATE.buildState(heroTemplate) };
  const axe = { combatant_id: "monster-1:axe", side: "monsters", position_ft: 90, state: window.IRON_PIT_BROWSER_STATE.buildState(axeTemplate) };
  const setup = { heroes: [hero], monsters: [axe] };
  const before = [hero.position_ft, axe.position_ft];
  window.IRON_PIT_DICE = deterministicDice(11);
  const turn = window.IRON_PIT_BROWSER_TURN.resolveTurn(1, 1, axe, setup);
  assert.ok(turn.events.some((event) => event.event_type === "attack"), "fixed Pit melee attacks without a closing turn");
  assert.equal(turn.events.some((event) => event.event_type === "movement" || event.event_type === "dash" || event.feature_id === "dodge"), false);
  assert.deepEqual([hero.position_ft, axe.position_ft], before, "fixed Pit combat never relocates cards for ordinary closing");
}

{
  const battle = fight(["karnok-stoneward-l1"], ["srd-black-bear"], queuedDice([1, 20, 15, 1, 15, 1]));
  const strikes = battle.events.filter((event) => event.round_number === 1 && event.event_type === "attack" && event.actor_id.startsWith("monster-1:"));
  assert.equal(strikes.length, 2, "Black Bear should make two Rend attacks");
  assert.deepEqual(strikes.map((event) => event.weapon_id), ["black-bear-rend", "black-bear-rend"]);
}

{
  const battle = fight(["karnok-stoneward-l1"], ["srd-brown-bear"], queuedDice([1, 20, 15, 1, 15, 1]));
  const strikes = battle.events.filter((event) => event.round_number === 1 && event.event_type === "attack" && event.actor_id.startsWith("monster-1:"));
  assert.deepEqual(strikes.map((event) => event.weapon_id), ["brown-bear-bite", "brown-bear-claw"]);
  assert.ok(strikes[1].applied_condition_ids?.includes("prone"), "Brown Bear Claw should knock a surviving Large-or-smaller target Prone");
}

{
  const heroTemplate = structuredClone(window.IRON_PIT_BROWSER_HEROES["karnok-stoneward-l1"]);
  const boarTemplate = structuredClone(window.IRON_PIT_BROWSER_MONSTERS["srd-boar"]);
  const hero = { combatant_id: "hero-1:karnok", side: "heroes", position_ft: 0, state: window.IRON_PIT_BROWSER_STATE.buildState(heroTemplate) };
  const boar = { combatant_id: "monster-1:boar", side: "monsters", position_ft: 30, state: window.IRON_PIT_BROWSER_STATE.buildState(boarTemplate) };
  hero.state.initiative_total = 10;
  boar.state.initiative_total = 20;
  const setup = { heroes: [hero], monsters: [boar] };
  const before = [hero.position_ft, boar.position_ft];
  window.IRON_PIT_BROWSER_STATE.beginTurn(boar.state);
  window.IRON_PIT_DICE = deterministicDice(11);
  const charged = window.IRON_PIT_BROWSER_CHARGE.resolveClosing(1, 1, boar, hero, setup);
  assert.equal(charged.handled, true);
  assert.equal(charged.events.length, 1, "Charge resolves from the pre-contact run-up without a movement event");
  assert.equal(charged.events[0].feature_id, "charge");
  assert.equal(charged.events[0].damage_roll.notation, "1d6+1 + 1d6+0");
  assert.ok(charged.events[0].applied_condition_ids.includes("prone"));
  assert.deepEqual([hero.position_ft, boar.position_ft], before);
}

{
  const heroTemplate = structuredClone(window.IRON_PIT_BROWSER_HEROES["karnok-stoneward-l1"]);
  const boarTemplate = structuredClone(window.IRON_PIT_BROWSER_MONSTERS["srd-boar"]);
  const hero = { combatant_id: "hero-1:karnok", side: "heroes", position_ft: 0, state: window.IRON_PIT_BROWSER_STATE.buildState(heroTemplate) };
  const boar = { combatant_id: "monster-1:boar", side: "monsters", position_ft: 5, state: window.IRON_PIT_BROWSER_STATE.buildState(boarTemplate) };
  boar.state.current_hp = 6;
  window.IRON_PIT_DICE = queuedDice([4, 15, 3]);
  const event = window.IRON_PIT_BROWSER_ATTACK.resolveAttack(1, 1, boar, hero, boarTemplate.attacks[0], 5);
  assert.equal(event.attack_roll.mode, "advantage");
  assert.equal(event.attack_roll.selected_roll, 15);
}

{
  const battle = fight(["rokhan-stonefury-l1"], ["srd-commoner"], queuedDice([20, 1, 15, 6, 6]));
  const rage = battle.events.find((event) => event.actor_id.startsWith("hero-1:") && event.feature_id === "rage");
  const attack = battle.events.find((event) => event.actor_id.startsWith("hero-1:") && event.event_type === "attack");
  assert.ok(rage, "audited Barbarian should Rage in combat");
  assert.equal(attack?.weapon_id, "rokhan-greataxe");
  assert.equal(attack?.damage_roll?.modifier, 5, "Rokhan should add +3 Strength and +2 Rage damage");
}

{
  const state = {
    template: { resources: { breath: 1 } }, resources: { breath: 1 }, action_available: true,
    is_dead: false, is_unconscious: false, active_effect_ids: [],
  };
  const target = {
    combatant_id: "hero-1:target", state: {
      template: { name: "Target", saving_throw_bonuses: { dexterity: 0 } }, active_effect_ids: [],
      current_hp: 20, temporary_hp: 0, death_save_successes: 0, death_save_failures: 0,
      is_alive: true, is_dead: false, is_unconscious: false, concentration: null,
    },
  };
  const actor = { combatant_id: "monster-1:dragon", state: { ...state, template: { ...state.template, name: "Test Dragon" } } };
  const action = { id: "breath", name: "Test Breath", saveAbility: "dexterity", dc: 12, range: 15,
    damageDiceCount: 0, damageDiceSize: 6, damageBonus: 0, successDamage: "none", resourceId: "breath", resourceCost: 1 };
  window.IRON_PIT_DICE = queuedDice([10]);
  const event = window.IRON_PIT_BROWSER_SAVES.resolveAction(1, 1, actor, target, action, 5);
  assert.equal(event.resource_remaining, 0, "save action spends its shared resource exactly once");
  assert.equal(window.IRON_PIT_BROWSER_SAVES.resourceAvailable(actor.state, action), false);
  assert.throws(() => window.IRON_PIT_BROWSER_SAVES.resolveAction(2, 2, actor, target, action, 5, { spendAction: false }), /resource is unavailable/);
}

{
  const member = { combatant_id: "monster-1:dragon", state: {
    template: { name: "Test Dragon", resources: { breath: 1 }, resource_recharges: {
      breath: { name: "Test Breath", minimum: 5, maximum: 6, dieSize: 6 },
    } }, resources: { breath: 0 },
  } };
  window.IRON_PIT_DICE = queuedDice([5]);
  const recharge = window.IRON_PIT_BROWSER_RECHARGE.resolve(7, 2, member);
  assert.equal(recharge.sequence, 8);
  assert.equal(member.state.resources.breath, 1);
  assert.equal(recharge.events[0].resource_remaining, 1);
  assert.match(recharge.events[0].description, /Test Breath/);
}

{
  const heroes = Array(6).fill("karnok-stoneward-l1");
  const monsters = Array(6).fill("srd-wolf");
  const battle = fight(heroes, monsters, deterministicDice(42));
  assert.notEqual(battle.outcome, "active");
  assert.ok(battle.rounds <= 100);
  assert.equal(battle.setup.heroes.length, 6);
  assert.equal(battle.setup.monsters.length, 6);
  assert.throws(() => fight(Array(7).fill("karnok-stoneward-l1"), ["srd-wolf"]), /1-6 cards per side/);
}

console.log("Browser combat regressions passed.");
