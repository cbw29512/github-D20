# Iron Pit Arena Policy

`docs/IRON_PIT_UNIVERSAL_COMBAT_DOCTRINE.md` is authoritative. This file specializes that doctrine for battlefield geometry and autonomous pawn behavior.

Iron Pit is a deterministic card-vs-card D&D combat-math simulator. It is not a complete tactical virtual tabletop.

## Universal combatant rule

Heroes, monsters, and future homebrew use one combat engine. Strength, Armor Class, Initiative, attack rolls, saving throws, Advantage/Disadvantage, damage, healing, defenses, resources, action economy, and every other supported mathematical primitive mean the same thing regardless of card type.

Source cards/templates are immutable. Starting a fight creates disposable runtime state. Current HP, Temporary HP, buffs, debuffs, conditions, resources, recharge state, Concentration, and temporary modifiers may change during combat but must never permanently rewrite the source card.

## Standard board geometry

The standard Iron Pit is fixed at **3 columns x 4 rows = 12 combat slots**.

- One half belongs to monsters: **6 slots**.
- One half belongs to pregens/heroes: **6 slots**.
- Existing D&D five-foot-square distance conventions remain the working distance convention unless later explicitly changed.
- The board exists to make engagement, range, reach, adjacency, target legality, area targeting, and simple closing deterministic.
- Creature size may still matter when a rule explicitly checks size, but the current Pit is not a free-form tactical packing/pathfinding simulator.

## Slug-fest behavior

Combatants are autonomous pawns compelled to fight until one side is dead.

There is no morale, surrender, voluntary retreat, fleeing, kiting, or keep-away AI.

When comparing legal offensive options, a pawn chooses the option with the highest expected damage after relevant known combat math such as:

- hit probability;
- saving-throw probability;
- Advantage/Disadvantage;
- target count;
- known resistance, immunity, vulnerability, and damage reduction;
- legal resource/recharge availability.

Do not choose based only on the largest possible die result. Limited-use and recharge offense is available for the current fight and is not hoarded for a future encounter.

If a damaging option is unavailable only because engagement has not occurred, the pawn closes or Dashes toward the fight. Once engaged, it does not voluntarily retreat to manufacture ranged distance.

Non-offensive healing/support/control choices are governed only by shared universal policies. Never create a monster-name-specific tactical planner.

## Movement boundary

Iron Pit keeps only the movement facts required for simple engagement and action legality.

- Base position, range, reach, adjacency, and closing distance remain relevant.
- Movement-only Speed changes, forced movement, dragging, pushing, pulling, climbing, swimming, flying, burrowing, repositioning, standing-cost, and similar movement consequences do not block certification by themselves.
- If an ability combines movement with a supported combat-math consequence, ignore only the movement component and model the supported consequence.
- Example: an effect that knocks a target Prone and reduces Speed keeps Prone's attack-math consequences but ignores the Speed consequence.
- There is no tactical pathfinding/spacing optimizer at this stage.

This is a deliberate product simplification, not a claim about full tabletop D&D tactics.

## Range, reach, and adjacency are not movement-only effects

Weapon/spell range, melee reach, adjacency, and target legality remain in scope because they determine whether a chosen combat action can legally resolve on the fixed Pit board.

A movement modifier is not allowed to become a hidden certification blocker merely because a full tactical simulator could turn that Speed change into a different future position. The current Pit deliberately abstracts that indirect tactical layer.

## Conditions use universal math

Conditions are source states that contribute reusable universal effects.

Example: Prone contributes:

- Disadvantage on the Prone creature's attack rolls;
- Advantage on attacks against it from within 5 feet;
- Disadvantage on attacks against it from farther than 5 feet;
- movement/standing-cost consequences ignored by the current movement abstraction.

Those roll effects use the same Advantage/Disadvantage engine as every spell, trait, class feature, monster ability, and homebrew source. The combat log retains `Prone` as the source name.

## Advantage / Disadvantage

Multiple sources never create custom variants:

- any number of Advantage sources -> Advantage;
- any number of Disadvantage sources -> Disadvantage;
- at least one of each -> normal roll.

Runtime/audit data should preserve contributing source names even though the mathematical resolver is shared.

## Aquatic-only creatures

Aquatic-only creatures that cannot meaningfully participate in the standard land Pit are **deferred environment content**, not unresolved universal engine work.

Use an explicit environment deferral such as `deferred-environment:aquatic-only`. Do not spend current implementation time creating aquatic tactical behavior. A future aquatic arena can reuse the same universal combat engine.

## Readiness rule

A card is blocked only by an unsupported consequence that changes actual Iron Pit combat math under this policy.

Movement-only riders, aquatic-only environment requirements, exploration/social/narrative effects, and other deliberately out-of-scope consequences do not block certification.

Unsupported in-scope combat math fails closed. Out-of-scope effects are intentionally ignored rather than approximated.
