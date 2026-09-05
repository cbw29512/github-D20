# Iron Pit Universal Combat Doctrine

This document is durable project law for Iron Pit combat architecture. It applies to SRD monsters, canonical pregens, future pregens, and homebrew. If an older document, checkpoint, implementation shortcut, or historical certification rule conflicts with this doctrine, this doctrine controls until the older material is reconciled. Only a later explicit user decision may change it.

## 1. Product intent

Iron Pit is a deterministic D&D combat-math engine, not a complete tactical virtual tabletop.

The long-term goal is one reusable combat engine that can accept new monsters, pregens, and homebrew without creating a bespoke resolver for each named ability. D&D source text supplies names, triggers, targets, resources, durations, and mathematical consequences. Shared engine primitives resolve those consequences.

The design rule is:

> Same combat outcome -> same engine primitive. Different source name -> different log/source metadata, not different math code.

Examples:

- Disadvantage is the same universal `disadvantage` mechanic no matter whether its source is Prone, Poisoned, Frightened, a spell, a monster trait, a class feature, or homebrew.
- Advantage is the same universal `advantage` mechanic regardless of source.
- `+2 AC`, a saving-throw bonus, typed bonus damage, resistance, healing, Temporary HP, action loss, recharge, and similar outcomes each use shared primitives rather than ability-specific resolvers.
- A source ability may contain several consequences. Each consequence is evaluated separately and mapped to a universal primitive or deliberately ignored by Pit scope.

Never create `MonsterNameAbilityResolver`, `ClassNameDisadvantage`, or another named-special-case resolver when the same mathematical result can be represented by an existing universal capability.

## 2. Source identity and engine identity are separate

The engine must preserve the exact D&D/homebrew source identity for auditability while resolving through universal mechanics.

A runtime effect conceptually carries at least:

- `source_name`: printed or authored ability/spell/trait name used in logs;
- `effect_type`: universal mathematical primitive;
- `trigger`: when the effect becomes active;
- `scope`: which rolls, targets, attacks, saves, damage, actions, or defenses it affects;
- `duration` / expiry trigger where applicable;
- `resource` / usage cost where applicable;
- source creature/card identity where needed.

Example:

`Frightful Presence -> disadvantage on attacks`

and

`Shadow Curse -> disadvantage on attacks`

must both use the same disadvantage resolver. The combat log still says `Frightful Presence` or `Shadow Curse` accurately.

Logs should explain the source and the resolved universal outcome, for example:

`Karnok attacks with Disadvantage (Prone).`

The log must never replace the real ability/condition name with an invented engine-only name when the source name is known.

## 3. Combat-math scope

The whole supported combat model is math. The question is not whether an effect has a familiar label; the question is what mathematical consequence it produces inside the deliberately simplified Pit.

For every printed effect, decompose it into consequences and ask whether each consequence changes any supported Pit quantity or legal combat opportunity, including:

- attack roll probability;
- saving throw probability;
- Advantage / Disadvantage;
- Armor Class;
- save DC or roll modifiers;
- damage dice, flat damage, damage type, critical behavior, recurring damage, target count, and area damage;
- resistance, immunity, vulnerability, damage reduction, damage prevention;
- current HP, maximum HP, healing, regeneration, Temporary HP;
- Action, Bonus Action, Reaction, Extra Attack, Multiattack, Legendary Action, or another supported action-economy opportunity;
- resource availability, spell slots, limited uses, recharge, or other resource gates that change legal combat output;
- conditions only through the mathematical consequences the Pit actually uses;
- range, reach, adjacency, and target legality where they determine whether a selected combat action can occur in the Pit.

If a consequence changes one of those values, it is in scope and must be represented accurately or remain a real blocker.

If a consequence is deliberately outside the simplified Pit model, it does not block certification.

## 4. Conditions are bundles of universal consequences

Conditions do not get private duplicate math. A condition is a named source state that contributes universal effects.

Example: Prone.

The relevant Pit consequences are:

- the Prone creature's attack rolls have Disadvantage;
- attacks against the Prone creature from within 5 feet have Advantage;
- attacks against the Prone creature from farther than 5 feet have Disadvantage;
- the movement/standing-cost portion is ignored by the current simplified Pit movement policy.

Those attack modifiers must flow through the same Advantage/Disadvantage resolver used by every other source.

The same decomposition rule applies to every condition, spell, trait, feat, class feature, monster ability, and homebrew feature.

## 5. Mixed abilities are evaluated component by component

Never classify an entire named feature as supported or unsupported merely because one part is out of scope.

Examples:

- `Prone + Speed becomes 0`: keep the Prone combat-math consequences; ignore the movement-only Speed consequence.
- `Push 10 feet + 2d6 damage`: resolve the damage; ignore the push unless a separately supported consequence depends on it.
- `Speed -10 + attacks have Disadvantage`: ignore Speed; apply universal Disadvantage.
- `Ray of Frost`: resolve the spell attack and cold damage; ignore the Speed reduction.
- `Fireball`: resolve target legality, Dexterity saves, fire damage, and half-on-success; ignore object ignition.

A harmless/out-of-scope rider never blocks an otherwise accurate damaging or combat-math ability.

## 6. Trigger, scope, duration, and source do not create new effect types

Two abilities that both cause Disadvantage still use one Disadvantage primitive even when they have different:

- triggers;
- targets;
- durations;
- expiry timing;
- resources;
- source names;
- creature types or classes.

For example, `until the end of the target's next turn` and `until the start of the source's next turn` are different duration metadata around the same underlying modifier, not separate disadvantage mechanics.

The same rule applies to numeric modifiers, defenses, healing, damage riders, action denial, and other universal outcomes.

## 7. Advantage / Disadvantage stacking is universal

Use the D&D Advantage/Disadvantage rule once for every source.

- Any number of Advantage sources still produces Advantage.
- Any number of Disadvantage sources still produces Disadvantage.
- At least one source of each cancels to a normal d20 roll.
- Keep all contributing source names in runtime/audit data so the log can remain accurate without inventing separate mathematical implementations.

## 8. The standard Iron Pit arena is a 3 x 4 slug-fest board

The standard Pit is fixed at 3 columns by 4 rows: 12 combat slots total.

- The monster side owns one half: 6 slots.
- The pregen/hero side owns the other half: 6 slots.
- The board exists to make engagement, adjacency, range, reach, area targeting, and closing-to-fight deterministic.
- It is not intended to become a full tactical movement simulator at this stage.
- Existing D&D five-foot-square distance conventions remain the working distance convention unless a later explicit policy changes them.

The battlefield is a slug-fest. Combatants are autonomous pawns compelled to fight rather than kite, flee, or play keep-away.

## 9. Movement policy

Base position, range, reach, and simple closing distance remain relevant because a creature may need to get into legal attack range.

However, movement-only effects are deliberately abstracted away at this stage.

- Do not block a card merely because an ability only changes Speed, pushes, pulls, drags, climbs, swims, flies, burrows, repositions, or otherwise changes movement with no additional supported combat-math consequence.
- If the same ability also changes attack/save probability, damage, HP, defenses, action economy, conditions with supported consequences, or another supported quantity, model those components and ignore only the movement component.
- If a pawn cannot currently make a legal damaging attack because it is outside range, it may Dash/close toward engagement under the simple arena policy.
- No voluntary retreat, kiting, fleeing, pathfinding game, or movement optimization loop is part of current Iron Pit AI.
- Movement-only tactical consequences that would exist in a full tabletop simulator are intentionally deferred so the Pit remains simple.

This is a deliberate abstraction, not a claim that movement is unimportant in normal D&D.

## 10. Autonomous pawn combat selection

Iron Pit combatants are not conserving resources for an adventuring day. They are autonomous pawns trying to win the current deathmatch.

When comparing legal offensive choices, prefer the option with the highest expected damage after relevant known combat math such as hit/save probability, Advantage/Disadvantage, target count, and known defenses.

- Do not choose an inferior attack merely because its printed maximum die result is larger.
- Limited-use and recharge offensive abilities are valid choices when available; do not hoard them for a future encounter.
- If no damaging option is legal only because engagement has not occurred, close/Dash toward the fight.
- Do not retreat or kite to protect a ranged routine.
- Non-offensive healing/support/control choices may be selected only through an explicit shared universal policy; do not add monster-specific tactical planners.

The combat-selection AI may remain intentionally simple even when the engine can accurately resolve more complex effects.

## 11. Aquatic-only creatures are deferred, not implementation debt

Aquatic-only creatures that cannot meaningfully participate in the standard land Pit are outside the current certification target.

Mark them as an explicit environment deferral such as `deferred-environment:aquatic-only`.

- Do not spend current implementation time building aquatic arena behavior.
- Do not count aquatic-only deferrals as unresolved combat-engine blockers.
- A later aquatic arena can reactivate them using the same universal combat engine.

## 12. Immutable source cards, mutable fight state

Monster, pregen, and homebrew definitions are immutable source cards/templates.

Starting combat creates disposable runtime state. During the fight, the engine may change:

- current HP;
- Temporary HP;
- active conditions;
- buffs/debuffs;
- effective AC/attack/save modifiers;
- resources and recharge state;
- Concentration and other temporary combat state.

Those changes must never permanently rewrite the source card. A new fight starts from the original definition again.

## 13. New content lifecycle

Every new SRD monster, pregen, or homebrew card follows the same pipeline:

`source definition -> parse/normalize -> decompose named abilities into consequences -> map consequences to universal capabilities -> compile runtime state -> Python reference certification -> browser parity -> generated assets -> public readiness`

Before adding code for a new named ability:

1. Inspect every consequence of the ability.
2. Search the capability registry for an equivalent mathematical outcome.
3. Reuse existing universal primitives wherever possible.
4. Add only missing general-purpose primitives, never a card-name-specific shortcut.
5. Keep the original source name attached for logs/audit.
6. Re-audit all existing monsters/pregens because a new shared primitive may unlock many cards at once.

If two abilities have the same outcome, they must converge on the same capability even if their names and flavor are completely different.

## 14. Certification rule

A card is RAW-ready for the standard Pit when every supported-scope combat consequence can be accurately resolved by the shared engine and all permanent Python/browser/source/parity gates pass.

A card is not blocked by:

- movement-only riders;
- aquatic requirements when the whole creature is explicitly environment-deferred;
- exploration/social/narrative/object effects;
- other source text with no supported consequence in the current Pit abstraction.

A card remains blocked by an unsupported consequence that changes actual Pit combat math.

Unsupported combat-math consequences fail closed. Out-of-scope consequences are explicitly ignored, not approximated.

## 15. Architectural test for every future change

Before merging any combat feature, ask:

> If a different monster, pregen, or homebrew feature produced exactly this same mathematical outcome under a different name, would it use this exact same engine primitive?

If the answer is no, the design is probably too specific and should be generalized before certification.
