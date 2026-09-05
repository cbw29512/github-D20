# Iron Pit canonical combat loop

This document is authoritative for Iron Pit turn sequencing and AI action choice unless the user explicitly changes it.

Iron Pit is a deterministic card-vs-card damage simulator. Heroes and monsters use the same combat loop and the same universal math engine. Their differences are data: stats, attacks, spells, resources, damage riders, healing, defenses, and special damage abilities.

## Encounter start

1. Build combatants from certified card data.
2. Apply legal precombat/passive buffs that are part of the selected build or stat block and that affect damage/survival math.
3. Roll Initiative for every combatant and establish initiative order.
4. Determine whether the initiative winner qualifies for an opening special such as Charge, Pounce, or another printed first-contact damage ability. These specials use their own legal conditions; Iron Pit never invents extra damage.

## Stacked formation and movement abstraction

The Pit is a card-vs-card formation, not a free-movement battlefield. Frontline melee cards begin effectively engaged with the opposing frontline, while ranged combatants and casters are stacked immediately behind them.

- Ordinary Walk, Fly, Swim, Burrow, and Climb rates do not determine normal action legality or certification.
- Movement-only buffs, debuffs, pushes, pulls, dragging, and pathfinding are ignored unless another supported combat-math consequence depends on them.
- A source creature with no usable movement mode at all may be deferred as an eligibility edge case.
- A temporary runtime Speed of 0 never removes a creature from combat and never changes roster eligibility.
- Grappled therefore remains a combat condition without treating its Speed 0 consequence as removal: attacks against the grappler are normal absent other sources, while attacks against another creature have Disadvantage.
- Charge/Pounce and similar opening effects retain their printed attack/save/damage consequences through the dedicated opening abstraction rather than literal movement geometry.

## Turn loop

At the start of each combatant's turn:

1. Resolve mandatory ongoing damage, condition consequences that directly alter legal damage resolution, resource refresh/recharge timing, and death/incapacitation state.
2. Check survival actions. If a legal healing ability/spell is configured for the combatant and the configured threshold is met (normally Bloodied or an ally at 0 HP), resolve the healing according to its action economy and resource cost.
3. Check an eligible opening special such as Charge/Pounce when its initiative/round requirements are satisfied.
4. Choose the combat mode from the card data:
   - melee attacker;
   - ranged attacker;
   - caster;
   - hybrid, which chooses the highest-value currently legal damaging option according to the same deterministic policy.

### Melee

1. Select the configured melee attack or Attack/Multiattack sequence against a legal frontline target.
2. Roll to hit when the action uses an attack roll.
3. On a hit, roll and apply all damage components.
4. Apply any special weapon/mastery/feature damage component whose printed conditions are satisfied.
5. Spend action/resources and continue any legal Extra Attack/Multiattack sequence.

Ordinary closing movement is not simulated; melee contact is part of the stacked formation abstraction.

### Ranged

1. Use the configured ranged attack against a legal target in the stacked formation.
2. Roll to hit when required.
3. On a hit, roll and apply all damage components.
4. Apply any conditional special damage rider whose printed conditions are satisfied.
5. Spend action/resources and continue any legal Extra Attack/Multiattack sequence.

Ranged combatants stay behind their frontline and continue using legal ranged options. Iron Pit does not create kiting or retreat behavior.

### Caster

1. Enumerate currently legal damaging spells with available slots/resources and legal targets.
2. Prefer the highest spell level that can currently be cast.
3. Within that level, select the deterministic highest-value legal damaging option.
4. Resolve its attack roll or saving throw, then its damage components and legal target count/area.
5. Apply only damage/survival mechanics required by the Iron Pit damage-scope policy; ignore unrelated secondary riders.
6. Spend the correct spell slot/resource/action cost.

Cantrips remain available when no leveled damaging spell can legally be cast. Cantrip damage scaling follows character level.

## End of turn / next initiative

1. Resolve end-of-turn ongoing damage, expiry, death, healing/HP state, and only those conditions needed by supported damage/survival math.
2. Advance to the next living combatant in initiative order.
3. At the end of the initiative list, increment the round and repeat.
4. Continue until one side has no living combatants.

## Universal engine rule

Heroes and monsters never receive separate combat engines. Equivalent math uses the same resolver regardless of source.

Examples:

- Fighter greatsword and monster claw: attack-roll damage.
- Fireball and dragon breath: saving-throw area damage.
- Sneak Attack and venom: conditional extra damage components.
- Extra Attack and Multiattack: repeated attack sequence.
- Second Wind and monster healing: healing/resource math.
- Spell slots and Recharge/Uses per Day: resource constraints on legal damage frequency.

A new class feature, spell, weapon ability, or monster ability should create new engine code only when it introduces a genuinely new damage/survival mathematical primitive. Otherwise it is data.

## Scope guard

Do not expand the turn loop for secondary riders that do not matter to damage/survival resolution. Legacy support for broader conditions or movement may remain if already tested, but it must not complicate certification of otherwise-correct damaging abilities.
