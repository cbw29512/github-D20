(() => {
  "use strict";

  const HERO_BACK = 0, HERO_FRONT = 5, MONSTER_FRONT = 10, MONSTER_BACK = 15;
  const attacks = (template) => template?.attacks || [];
  const alive = (member) => member.state.is_alive && !member.state.is_dead && member.state.current_hp > 0;
  const X = () => window.IRON_PIT_BROWSER_RESOURCES || { available: () => true };

  function hasRangedWeaponOffense(template) {
    return attacks(template).some((attack) => attack.kind === "ranged" && Number.isFinite(attack.long) && attack.long > 5);
  }
  function primaryWeaponIsRanged(template) {
    const primary = attacks(template).find((attack) => attack.id === template?.primary_attack_id) || attacks(template)[0];
    return primary?.kind === "ranged" && Number.isFinite(primary.long) && primary.long > 5;
  }
  function hasRangedSpellOffense(template) {
    if ((template?.spell_attack_actions || []).some((action) => action.attackKind === "ranged" && (action.range || 0) > 5)) return true;
    return (template?.spell_save_actions || []).some((action) => (action.range || 0) > 5);
  }
  function hasTrueRangeOffense(template) { return hasRangedWeaponOffense(template) || hasRangedSpellOffense(template); }
  function usesBackline(template) { return primaryWeaponIsRanged(template) || hasRangedSpellOffense(template); }
  function isBackline(member) { return usesBackline(member.state.template); }

  function startingPosition(template, side) {
    const back = usesBackline(template);
    if (side === "heroes") return back ? HERO_BACK : HERO_FRONT;
    if (side === "monsters") return back ? MONSTER_BACK : MONSTER_FRONT;
    throw new Error(`Unknown encounter side: ${side}`);
  }
  function enemies(member, setup) { return member.side === "heroes" ? setup.monsters : setup.heroes; }
  function livingTargets(member, setup) {
    const pool = enemies(member, setup), active = pool.filter(alive);
    if (active.length) return active;
    return pool.filter((target) => target.state.template.kind === "character"
      && target.state.is_alive && !target.state.is_dead && target.state.current_hp === 0);
  }
  function targetOrder(member, setup, preferBackline = false) {
    const targets = livingTargets(member, setup);
    const front = targets.filter((target) => !isBackline(target));
    const back = targets.filter(isBackline);
    return preferBackline ? [...back, ...front] : [...front, ...back];
  }
  function hasFrontlineTarget(member, setup) { return livingTargets(member, setup).some((target) => !isBackline(target)); }
  function hasBacklineTarget(member, setup) { return livingTargets(member, setup).some(isBackline); }
  function alliedFrontlineActive(member, setup) {
    const allies = member.side === "heroes" ? setup.heroes : setup.monsters;
    return allies.some((ally) => ally !== member && alive(ally) && !isBackline(ally));
  }
  function targetAllowed(member, target, attack) {
    if (!attack.forbidSelfGrappledTarget) return true;
    return !target.state.grapple_sources.some((source) => source.source_id === member.combatant_id);
  }
  function resourceAvailable(member, attack) {
    return !attack.resourceId || X().available(member.state, attack.resourceId, attack.resourceCost || 1);
  }
  function attackDistance(member, target, attack) {
    const actual = Math.abs(member.position_ft - target.position_ft);
    if (attack.kind === "melee") return Math.min(actual, attack.reach || 5);
    const normal = Number.isFinite(attack.normal) ? attack.normal : attack.long;
    if (!Number.isFinite(normal)) throw new Error(`Ranged attack ${attack.id} has no normal range.`);
    return Math.min(actual, normal);
  }
  function saveDistance(member, target, range) { return Math.min(Math.abs(member.position_ft - target.position_ft), range); }
  function chooseAttack(member, setup, ids, kind = null, preferBackline = false) {
    const allowed = new Set(ids);
    const profiles = attacks(member.state.template).filter((attack) => allowed.has(attack.id)
      && (!kind || attack.kind === kind) && resourceAvailable(member, attack));
    for (const target of targetOrder(member, setup, preferBackline)) {
      const attack = profiles.find((profile) => targetAllowed(member, target, profile));
      if (attack) return { target, attack, distance: attackDistance(member, target, attack) };
    }
    return null;
  }
  function chooseResourceBackedAttack(member, setup) {
    const ids = attacks(member.state.template).filter((attack) => attack.resourceId).map((attack) => attack.id);
    return ids.length ? chooseAttack(member, setup, ids) : null;
  }
  function chooseStandardAttack(member, setup) {
    const ids = attacks(member.state.template).map((attack) => attack.id);
    if (isBackline(member) && alliedFrontlineActive(member, setup)) {
      const ranged = chooseAttack(member, setup, ids, "ranged");
      if (ranged) return ranged;
    }
    return chooseAttack(member, setup, ids, "melee") || chooseAttack(member, setup, ids, "ranged");
  }
  function flexibleSlotHasBoth(member, ids) {
    const allowed = new Set(ids), kinds = new Set(attacks(member.state.template)
      .filter((attack) => allowed.has(attack.id) && resourceAvailable(member, attack)).map((attack) => attack.kind));
    return kinds.has("melee") && kinds.has("ranged");
  }
  function backlineHoldsPosition(member, setup) {
    return isBackline(member) && alliedFrontlineActive(member, setup) && hasRangedWeaponOffense(member.state.template);
  }

  window.IRON_PIT_BROWSER_FORMATION = {
    hasRangedWeaponOffense, hasTrueRangeOffense, usesBackline, isBackline, startingPosition,
    targetOrder, hasFrontlineTarget, hasBacklineTarget, alliedFrontlineActive, targetAllowed,
    attackDistance, saveDistance, chooseAttack, chooseResourceBackedAttack, chooseStandardAttack,
    flexibleSlotHasBoth, backlineHoldsPosition,
  };
})();
