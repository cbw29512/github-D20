"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = globalThis;
const load = (name) => vm.runInThisContext(fs.readFileSync(path.join(__dirname, name), "utf8"), { filename: name });
for (const file of [
  "browser-condition-immunity.js", "browser-condition-rules.js", "browser-action-economy.js",
  "browser-resources.js", "browser-grapple.js", "browser-state.js", "browser-formation.js",
  "browser-standard-attack-action.js", "browser-turn.js",
]) load(file);

const F = window.IRON_PIT_BROWSER_FORMATION;
const S = window.IRON_PIT_BROWSER_STATE;
const E = window.IRON_PIT_ACTION_ECONOMY;
const X = window.IRON_PIT_BROWSER_RESOURCES;
const blade = { id: "blade", name: "Blade", kind: "melee", reach: 5 };
const bow = { id: "bow", name: "Bow", kind: "ranged", long: 80, normal: 80 };
const melee = { kind: "character", primary_attack_id: "blade", attacks: [blade] };
const meleeWithBackupRange = { kind: "character", primary_attack_id: "blade", attacks: [blade, bow] };
const ranged = { kind: "character", primary_attack_id: "bow", attacks: [bow, blade] };
const rangedCaster = { kind: "character", primary_attack_id: "staff", attacks: [{ id: "staff", kind: "melee" }], spell_save_actions: [{ range: 60 }] };

assert.equal(F.startingPosition(melee, "heroes"), 5);
assert.equal(F.startingPosition(melee, "monsters"), 10);
assert.equal(F.startingPosition(meleeWithBackupRange, "heroes"), 5);
assert.equal(F.startingPosition(ranged, "heroes"), 0);
assert.equal(F.startingPosition(ranged, "monsters"), 15);
assert.equal(F.startingPosition(rangedCaster, "heroes"), 0);

function template(name, primary, attacks, kind = "character") {
  return {
    id: name.toLowerCase(), name, kind, size: "medium", max_hp: 10, speed_ft: 30,
    primary_attack_id: primary, attacks, traits: [], resources: {}, saving_throw_actions: [],
  };
}
const frontTemplate = template("Frontline", "blade", [blade]);
const archerTemplate = template("Archer", "bow", [bow, blade]);
const enemyFrontTemplate = template("Enemy Front", "blade", [blade], "monster");
const enemyBackTemplate = template("Enemy Back", "bow", [bow, blade], "monster");
const combatant = (id, side, position, tpl) => ({
  combatant_id: id, side, position_ft: position, state: S.buildState(structuredClone(tpl)),
});

const front = combatant("hero-front", "heroes", 5, frontTemplate);
const archer = combatant("hero-back", "heroes", 0, archerTemplate);
const enemyFront = combatant("monster-front", "monsters", 10, enemyFrontTemplate);
const enemyBack = combatant("monster-back", "monsters", 15, enemyBackTemplate);
const setup = { heroes: [front, archer], monsters: [enemyFront, enemyBack] };

assert.deepEqual(F.targetOrder(front, setup).map((member) => member.combatant_id), ["monster-front", "monster-back"]);
assert.equal(F.chooseStandardAttack(front, setup).attack.id, "blade", "frontline defaults to melee");
assert.equal(F.chooseStandardAttack(archer, setup).attack.id, "bow", "protected backline stays ranged");

front.state.current_hp = 0; front.state.is_alive = false; front.state.is_dead = true;
assert.equal(F.chooseStandardAttack(archer, setup).attack.id, "blade", "exposed ranged card switches to melee when possible");

window.IRON_PIT_BROWSER_ATTACK = {
  resolveAttack(sequence, round, attacker, target, attack) {
    E.spend(attacker.state, "action");
    return { sequence, round_number: round, event_type: "attack", actor_id: attacker.combatant_id,
      target_id: target.combatant_id, weapon_id: attack.id, description: `${attacker.state.template.name} attacks.` };
  },
};
archer.position_ft = 0;
enemyFront.position_ft = 100;
enemyFront.state.current_hp = 10; enemyFront.state.is_alive = true; enemyFront.state.is_dead = false;
const before = [archer.position_ft, enemyFront.position_ft, enemyBack.position_ft];
const turn = window.IRON_PIT_BROWSER_TURN.resolveTurn(1, 1, archer, setup);
assert.equal(turn.events.find((event) => event.event_type === "attack").weapon_id, "blade");
assert.equal(turn.events.some((event) => event.event_type === "movement" || event.event_type === "dash"), false);
assert.deepEqual([archer.position_ft, enemyFront.position_ft, enemyBack.position_ft], before);

const rockResource = "test-rock-recharge";
const rock = { id: "rock", name: "Rock", kind: "ranged", normal: 25, long: 50, resourceId: rockResource, resourceCost: 1 };
const apeTemplate = template("Ape", "blade", [blade, rock], "monster");
apeTemplate.resources = { [rockResource]: 1 };
const ape = combatant("monster-ape", "monsters", 10, apeTemplate);
const target = combatant("hero-target", "heroes", 5, frontTemplate);
const apeSetup = { heroes: [target], monsters: [ape] };
let limited = F.chooseResourceBackedAttack(ape, apeSetup);
assert.equal(limited.attack.id, "rock");
S.beginTurn(ape.state);
window.IRON_PIT_BROWSER_STANDARD_ATTACK_ACTION.resolve(20, 1, ape, target, limited.attack, limited.distance, apeSetup, "1:ape");
assert.equal(X.uses(ape.state, rockResource), 0);
assert.equal(F.chooseResourceBackedAttack(ape, apeSetup), null);
X.restore(ape.state, rockResource);
limited = F.chooseResourceBackedAttack(ape, apeSetup);
assert.equal(limited.attack.id, "rock");

console.log("Fixed-formation and limited-attack browser policy regressions passed.");
