# Monster Certification Ladder

Iron Pit expands the SRD roster from the simplest combat math upward. A tranche advances only after the exact branch head passes the full Python/browser/static certification suite.

## Promotion rule

1. Add the smallest shared combat-math primitive required by the current low-complexity tranche.
2. Express monsters as declarative data whenever existing primitives are sufficient.
3. Run source audit, Python parity, browser parity, generated-static parity, and production-path gates.
4. If a tranche fails, fix the shared primitive or source data before adding more monsters.
5. Only after a green tranche move to the next complexity tier.

## Tier 1 — low CR, single/simple blocker

Priority candidates:

- Ape — Recharge-backed ranged attack. Current proof case.
- Stirge — attached target plus recurring damage.
- Spy — inspect Bonus Action; ignore it if it is movement/non-math only, otherwise model the math consequence.
- Wight — inspect its single save/complex-action blocker and certify if it composes existing primitives.
- Ghoul — attack rider with Constitution save into temporary Paralyzed.

## Tier 2 — low CR, reusable conditions/control

- Giant Frog
- Giant Toad
- Hill Giant
- Merrow
- Roper
- Tough Boss
- Ankheg

Prefer shared Grappled, Restrained, Poisoned, Prone, recurring damage, and attack-modifier components. Do not create creature-specific resolvers.

## Tier 3 — simple traits and moderate CR

Work through monsters unlocked by reusable traits such as:

- Magic Resistance
- Regeneration
- Bloodied/conditional attack Advantage
- damage auras or start-turn damage
- simple limited-use/recharge actions

Environmental-only traits remain ignored or excluded according to arena policy.

## Tier 4 — composed mid/high CR

Certify monsters whose apparent complexity is mostly a composition of already-green primitives: Multiattack, saves, Recharge, conditions, damage defenses, resources, and real allies.

## Tier 5 — complex last

Defer until the shared engine is mature:

- spell-heavy monsters
- Legendary Actions / Legendary Resistance families
- lair-dependent math
- unusual possession, splitting, swallowing, body-sharing, or bespoke state-transfer mechanics
- rare edge cases that would otherwise distort the universal engine

## Architecture rule

If it is the same combat math, it uses the same resolver. Named monster abilities provide triggers, parameters, resources, and display names; universal combat primitives perform the math.
