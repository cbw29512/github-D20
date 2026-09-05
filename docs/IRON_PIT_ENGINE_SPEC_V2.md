# Iron Pit Engine Specification v2

This document is the authoritative architecture contract for the next Iron Pit combat engine. Older plans, checkpoints, and implementation behavior must be reconciled to this specification before they are treated as design authority.

## Product goal

Iron Pit is a deterministic D&D 2024 / SRD 5.2.1 card-vs-card combat-math simulator. It is intentionally not a complete tabletop simulator.

The engine targets broad coverage of the canonical monster and pregen catalogs, not 100 percent support for every bespoke rule. A rare or unusually complex combat-math mechanic may be explicitly deferred rather than forcing special-case architecture.

Aquatic/environment-dependent combat is excluded from the current target. Aquatic-only text is ignored when mathematically irrelevant; a creature whose meaningful combat behavior fundamentally depends on aquatic rules may be deferred.

## Governing combat-math test

Model a rule only when it changes the probability, amount, frequency, timing, legality, prevention, or recovery of damage or HP in the Iron Pit loop.

- In-scope examples: attack/save Advantage or Disadvantage, AC, attack/save modifiers, damage, critical rules, resistance/immunity/vulnerability, healing, Temporary HP, regeneration, action denial/grants, legal attack count, Recharge, limited-use resources, concentration, recurring damage, repeat saves, and combat-math-relevant conditions.
- Out-of-scope examples: water breathing, movement-only slow, terrain with no mathematical consequence, object interaction, narrative/exploration/social effects, and forced movement that never changes later legal damage.
- If an effect is genuinely ambiguous, do not guess. Flag it for user arbitration or defer it.

## One engine, shared mechanics

Heroes and monsters use the same combat-math engine. Strength is Strength, Advantage is Advantage, Prone is Prone, Recharge is Recharge, and resistance is resistance regardless of the name or source of the ability.

Named abilities exist for source identity, display, logging, triggers, parameters, and composition. They do not own duplicate implementations of standard mechanics.

Example:

- `Wolf Trip` may log as `Wolf Trip`, but if its effect knocks a target Prone it references the one shared `PRONE` mechanic.
- `Pack Tactics` and `Reckless Attack` may have different conditions and logs, but any granted Advantage resolves through the same shared `ADVANTAGE` mechanic.
- Ten differently named abilities that impose Prone all reference the same Prone implementation.

### Required architecture

`ability/card data -> trigger + conditions + resource rules + shared mechanic references -> small universal resolvers -> runtime state`

The central combat loop orchestrates events. It must not become a catalog of monster/class name conditionals.

A named ability may compose multiple shared mechanics. Example Pounce can compose attack, damage, saving throw, and Prone without requiring a bespoke `PounceResolver` if those mechanics are already expressible generically.

A bespoke resolver is acceptable only when a mechanic is genuinely unique, mathematically important, common/valuable enough to support, and explicitly justified. Otherwise flag/defer it.

## Capability disposition

Every audited ability/effect receives one of these outcomes:

- `SUPPORTED`: completely representable by current shared mechanics.
- `BUILD_SHARED_PRIMITIVE`: recurring combat math worth implementing once for many cards.
- `DEFERRED_COMPLEX_EDGE_CASE`: mathematically relevant but too bespoke/complex or too isolated to justify current architecture cost.
- `IGNORED_NON_MATH`: does not affect Iron Pit combat math.
- `EXCLUDED_ENVIRONMENT`: depends materially on excluded aquatic/environmental combat.

Certification must report the exact missing mechanic instead of broad labels such as `legendary`, `condition`, or `complex action`.

## Immutable card lifecycle

Card/source definitions are immutable.

Each fight creates disposable runtime state containing current HP, Temporary HP, spent resources, recharge availability, active buffs/debuffs, conditions, concentration, timing state, and other fight-local values.

Temporary effects may alter effective values and may be displayed on the card during combat, but they never write back to canonical card/source data.

Combat ending destroys runtime state. A new fight starts fresh from the immutable card definition, except for the allowed precombat buff procedure described below.

## Shared mechanic families

The engine should prefer small reusable modules/resolvers for recurring mechanics, including at minimum:

- D20 roll resolution
- Advantage / Disadvantage
- attack rolls
- saving throws
- critical hits / critical range
- typed damage components
- resistance / immunity / vulnerability
- damage reduction/prevention
- healing
- Temporary HP
- zero-HP/death handling
- action / Bonus Action / Reaction economy
- Extra Attack / Multiattack
- resource pools
- once-per-turn / once-per-round usage
- Recharge X-Y
- spell slots and other limited uses
- concentration
- timed modifiers/effects
- start/end-turn effects
- recurring damage and repeat saves
- Legendary Action pools/timing
- fixed-initiative events
- combat-math-relevant conditions such as Prone
- conditional damage/attack/save modifiers
- regeneration

Adding a new monster or pregen that uses existing mechanics should normally require data/reference changes, not new core combat code.

## Timing/event model

The engine must expose explicit timing windows rather than hiding all behavior inside one monolithic turn function.

Required conceptual events:

- `PRECOMBAT`
- `INITIATIVE`
- `FIXED_INITIATIVE_COUNT`
- `START_OF_TURN`
- `DURING_TURN`
- `BEFORE_ROLL`
- `AFTER_ROLL`
- `ON_HIT`
- `ON_CRITICAL`
- `ON_DAMAGE`
- `AFTER_ACTION`
- `END_OF_TURN`
- `AFTER_CREATURE_TURN`
- `ON_ZERO_HP`
- `ON_DEATH`
- `COMBAT_END`

Reaction timing and interrupt/after-trigger behavior must be preserved when it changes combat math.

Distinct frequency rules must remain distinct: once per attack, once per turn, once on your turn, once per round, fixed uses, spell/resource pools, and Recharge are not interchangeable cooldowns.

## Standard fight setup

1. Build fresh runtime state from immutable cards.
2. Resolve one legal precombat buff opportunity per combatant when applicable.
3. Roll Initiative.
4. Determine lair owner.
5. Determine whether approved opening abilities such as Charge/Pounce meet the Iron Pit initiative abstraction.
6. Enter the timed combat loop.

### Precombat buff

The precombat buff is runtime-only and does not mutate the source card. A buff that normally requires Concentration still obeys normal Concentration rules after combat begins. Competing legal buffs are chosen by the deterministic combat decision policy unless a card explicitly configures an opening choice.

## Lair ownership

There is at most one lair owner per fight.

- The highest-CR monster owns the lair.
- If multiple monsters tie for highest CR, the tied monster that wins Initiative owns the lair.
- If a further Initiative tie remains, the normal Iron Pit Initiative tie-break determines the owner.
- Only RAW/source lair-dependent combat-math abilities or resource changes activate. Lair ownership creates no invented bonus.
- If the lair owner dies, every remaining lair-only bonus/action/effect stops as soon as its rules allow the death to be recognized.
- Lair ownership never transfers. No second creature receives a lair bonus later in the fight.

Fixed-initiative lair actions, when supported by source data, resolve through the same fixed-initiative event system used by any other timed ability.

## Charge/Pounce/opening movement abstraction

Iron Pit does not simulate tactical run-up geometry.

When an opening Charge/Pounce-like ability requires movement/run-up only to unlock a combat-math consequence, winning Initiative may satisfy that opening prerequisite under Iron Pit policy. The printed attack, save, damage, target, size, condition, and resource consequences still resolve through their normal shared mechanics.

This is an Iron Pit prerequisite abstraction; it must not alter the underlying RAW mechanic such as Advantage, saving throws, damage dice, or Prone.

## Conditions

Conditions are decomposed into their in-scope mathematical consequences and reusable shared condition mechanics.

Example: ten named abilities imposing Prone all apply the same shared `PRONE` state. Logs retain the originating ability name.

Out-of-scope condition consequences are ignored rather than simulated. In-scope consequences such as attack Advantage/Disadvantage, action denial, automatic failed saves, resistance, or other damage/HP math are preserved.

## Allies and targeting

The engine never invents an ally to activate an ability. An ally-dependent effect requires an actual legal ally in the encounter.

Area/multi-target abilities use actual legal Iron Pit targets. Target count, friendly-fire rules, save/attack resolution, and damage are represented when they change encounter math. Non-mathematical geometry is not simulated beyond what is necessary to determine legal targets under the arena abstraction.

## Damage pipeline

Equivalent incoming damage uses one shared pipeline regardless of source. Exact ordering must be covered by tests and source-verified rules. Conceptually it includes:

`resolve hit/save -> determine damage components/critical behavior -> defenses/modifiers/reactions -> Temporary HP -> HP -> concentration/damage triggers -> zero-HP/death triggers`

No ability may bypass the shared damage pipeline merely because it is a class feature, spell, monster action, reaction, Legendary Action, or lair action.

## Decision policy

Combat AI is deliberately deterministic and mathematical, not role-play driven.

It selects legal options according to the configured combat policy, considering survival/healing needs, high-value limited/recharge abilities, damaging spells, Multiattack/Extra Attack, attacks, Bonus Actions, Reactions, and Legendary Actions without illegally using multiple mutually exclusive action-economy options.

A Recharge ability that becomes available again must be eligible for normal action selection; Recharge is rolled at its source-defined timing rather than approximated by a fixed cooldown.

## Logging

Logs must preserve the source-facing ability/action name and the shared mechanic consequence.

Example:

`Dire Wolf uses Bite. Target fails the Strength save and is knocked Prone.`

The implementation of Prone remains the same shared Prone mechanic used by every other source.

Logs must not imply that runtime effects permanently changed the underlying card.

## Pregen policy

The 12 canonical classes across levels 1-20 use the same shared mechanics as monsters. Class/subclass names determine available abilities and parameters, not alternate attack/save/damage implementations.

Expected recurring pregen families include resource pools, spell slots, action grants, healing, damage riders, once-per-turn damage, Advantage/Disadvantage, temporary AC/save/attack modifiers, concentration, reactions, Extra Attack, weapon mastery consequences, critical changes, and transformations only to the extent they change Iron Pit combat math.

A rare class/subclass feature may be deferred under the same rule as a rare monster ability.

## Monster policy

Monster traits, actions, Bonus Actions, Reactions, Legendary Actions, recharge abilities, limited-use actions, regeneration, ongoing effects, death triggers, HP thresholds, timed effects, spellcasting, defenses, and lair-dependent math are audited through the same shared mechanic vocabulary.

The monster source/audit path must not silently lose a combat-math ability merely because an older parser lacks a structured field for it. Raw/source text must remain available to detect unsupported relevant mechanics.

## Build and certification discipline

- Reuse existing correct shared code where it fits this specification.
- Refactor or bypass legacy code that duplicates a shared mechanic or encodes class/monster-name behavior.
- Prefer small modules with focused tests over a monolithic engine.
- Python and browser must implement the same mechanic semantics.
- Unsupported combat math fails closed or is explicitly deferred.
- Unsupported non-math text does not block a card.
- Do not deploy production during architecture work.
- Batch Git/CI work and avoid routine Netlify use.

## Verification checklist

Before calling the engine complete, rerun the full canonical catalogs:

- 330 SRD monsters
- 240 canonical pregen level snapshots

For every card, record supported shared mechanics, ignored non-math features, environment exclusions, and exact deferred blockers.

Then manually review representative examples of every shared mechanic family and verify logs identify the original ability while math routes through the shared resolver.
