# Iron Pit combat-math scope

`docs/IRON_PIT_UNIVERSAL_COMBAT_DOCTRINE.md` is the highest-authority combat architecture and scope document for this project. Read it first. This file exists as the required-read scope summary used by repository instructions and must not be interpreted more narrowly than the universal doctrine.

If this file, `docs/ARENA_POLICY.md`, an older master-plan checkpoint, historical certification logic, or implementation behavior conflicts with the universal doctrine, the universal doctrine controls until the older material is reconciled. Only a later explicit user decision may change that rule.

## Core rule

Iron Pit models the mathematical consequences of D&D combat through universal capabilities shared by monsters, pregens, and homebrew.

The permanent architecture rule is:

> Same combat outcome -> same engine primitive. Preserve the original source ability/condition/spell name separately for logs and audit.

Disadvantage is Disadvantage regardless of whether it came from Prone, Poisoned, Frightened, a spell, a monster ability, a pregen feature, or homebrew. The same applies to Advantage, AC modifiers, attack/save modifiers, damage, healing, defenses, action-economy changes, resources, and other supported mathematical outcomes.

A named ability is decomposed into individual consequences. Each consequence is independently mapped to a shared primitive or deliberately ignored under the current Pit abstraction. Do not make the whole ability a blocker merely because one secondary component is out of scope.

## Combat-math test

For every printed consequence, ask whether it changes a supported quantity inside the simplified Pit, including:

- attack/save probability, Advantage/Disadvantage, AC, save DC, or roll modifiers;
- damage amount/type, critical behavior, recurring damage, target count, or area damage;
- resistance, immunity, vulnerability, damage reduction/prevention;
- HP, maximum HP, healing, regeneration, Temporary HP;
- Action, Bonus Action, Reaction, Extra Attack, Multiattack, Legendary Action, or another supported combat opportunity;
- resources, slots, limited uses, or recharge that gate legal combat output;
- conditions through their supported mathematical consequences;
- range, reach, adjacency, and target legality needed to determine whether the chosen action can occur.

If yes, model it accurately or keep a real blocker. If no under the current Pit abstraction, ignore it explicitly rather than approximating it.

## Movement boundary

Iron Pit is intentionally not a complete tactical movement simulator yet.

- Base position, range, reach, adjacency, and simple closing-to-fight remain relevant.
- A pawn that cannot make a legal attack because it has not reached engagement may Dash/close toward the fight.
- Movement-only Speed changes, forced movement, dragging, climbing, swimming, flying, burrowing, retreat positioning, and similar tactical movement effects do not block certification by themselves.
- When a mixed ability contains both movement and another supported mathematical effect, ignore only the movement component and preserve the supported component.
- There is no voluntary retreat, kiting, fleeing, or pathfinding optimization loop.

Example: `Prone + Speed effect` keeps Prone's attack-math consequences while the movement/standing-cost consequence is ignored.

## Standard Pit

The standard arena is fixed at **3 columns x 4 rows = 12 combat slots**, split evenly into **6 monster slots** and **6 pregen/hero slots**. It is a slug-fest arena used to make engagement, range, reach, adjacency, area targeting, and simple closing deterministic, not to reproduce a full tactical map.

Aquatic-only creatures are explicitly deferred from the current standard land Pit. They are not current combat-engine implementation debt and should be marked as an environment deferral rather than treated as an unresolved universal mechanic.

## Conditions

Conditions are named bundles of reusable mathematical consequences, not separate private math engines.

For example, Prone currently decomposes into:

- the Prone creature's attack rolls -> universal Disadvantage;
- attacks against it from within 5 feet -> universal Advantage;
- attacks against it from farther than 5 feet -> universal Disadvantage;
- movement/standing cost -> ignored by current simplified movement policy.

The source name `Prone` remains visible in logs and runtime audit metadata.

## Source identity, duration, and trigger

Different source names, triggers, targets, durations, expiry rules, and resource costs do not justify duplicate outcome primitives.

An effect should carry source metadata plus its universal mathematical type. `Disadvantage until end of target turn` and `Disadvantage until start of source turn` are the same Disadvantage primitive with different duration metadata.

## Autonomous pawn policy

Iron Pit combatants are autonomous pawns compelled to fight the current deathmatch.

When comparing legal offensive choices, use the highest expected-damage option after relevant hit/save probability, Advantage/Disadvantage, target count, and known defenses. Do not hoard limited-use/recharge offense for a later encounter. If no damaging option is legal only because the pawn has not reached engagement, close/Dash toward the fight. Do not retreat or kite.

Non-offensive healing/support/control choices may be selected only through a shared universal policy; never add a monster-name-specific tactical planner.

## Immutable cards

Monster, pregen, and homebrew source cards/templates are immutable. Combat creates disposable runtime state. Buffs, debuffs, current HP, Temporary HP, active conditions, effective modifiers, Concentration, resources, and recharge state may change during the fight but must never permanently rewrite the source definition. A new fight starts from the original card again.

## New-content rule

Every new SRD monster, pregen, and homebrew addition follows the same lifecycle:

`source -> parse/normalize -> decompose consequences -> map to universal capabilities -> compile runtime -> Python reference -> browser parity -> generated assets -> public readiness`

Before adding code for a named ability, search for an equivalent mathematical outcome. Reuse the existing universal primitive when one exists. Add a new primitive only when the outcome itself is genuinely new and broadly reusable.

After adding a shared primitive, re-audit the full catalog because many cards may become certifiable at once.

Unsupported combat-math consequences fail closed. Out-of-scope consequences are explicitly ignored and do not block certification.
