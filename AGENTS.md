# D20 Iron Pit repository instructions

Before changing combat code, read these in order:

1. `docs/IRON_PIT_UNIVERSAL_COMBAT_DOCTRINE.md`
2. `docs/IRON_PIT_DAMAGE_SCOPE.md`
3. `docs/ARENA_POLICY.md`
4. `docs/IRON_PIT_MASTER_PLAN.md`
5. `docs/CANONICAL_COMBAT_BUILD_POLICY.md`
6. the structured certification manifests

`docs/IRON_PIT_UNIVERSAL_COMBAT_DOCTRINE.md` is the highest-authority combat architecture and scope document. If an older master-plan checkpoint, implementation shortcut, test assumption, historical certification rule, or other document conflicts with that doctrine, the doctrine controls until the older material is reconciled. Only a later explicit user decision may change it.

The repository, source records, permanent tests, and generated certification state are authoritative for current implementation state. Historical counts and chat checkpoints are not substitutes for exact-head repository evidence.

## Product and RAW rules

- D20 Iron Pit is a D&D 2024 / SRD 5.2.1 rules-first card-vs-card combat-math simulator.
- It is intentionally not a complete tactical virtual tabletop yet.
- Every exposed in-scope combat mechanic must be RAW within the deliberately simplified Pit abstraction.
- Unsupported **in-scope combat-math consequences** must fail closed.
- Deliberately out-of-scope consequences must be ignored explicitly rather than approximated and must not block certification.
- Never approximate, silently invent, or hand-wave combat math to make a hero or monster runnable.
- Prefer reusable universal engine mechanics over hero-, monster-, ability-, spell-, condition-, or level-specific hacks.
- Keep the Python reference engine and browser production engine behaviorally equivalent.
- Preserve deterministic combat regression coverage, source auditing and references, generated-static parity, exact-head CI certification, and repository-enforced production source-size limits.
- Never weaken, delete, bypass, or rewrite a test merely to make CI green. Fix the underlying defect. If an assertion is genuinely obsolete after an intentional architecture change, replace it with an equally strong assertion for the new contract.
- PR #32 must remain draft and unmerged. Do not merge it, merge to `main`, or change its base branch without explicit user authorization.

## Universal combat-capability rule

The permanent architecture rule is:

> Same combat outcome -> same engine primitive. Preserve the exact source ability/condition/spell/trait name separately for logs and audit.

Examples:

- Disadvantage is one universal mechanic regardless of whether its source is Prone, Poisoned, Frightened, a spell, a monster ability, a pregen feature, or homebrew.
- Advantage is one universal mechanic regardless of source.
- AC modifiers, attack/save modifiers, typed damage, healing, Temporary HP, resistance, immunity, vulnerability, action loss, resource use, recharge, and similar outcomes each use shared primitives.
- Different triggers, durations, targets, expiry rules, resources, or source names are metadata around the same outcome primitive; they do not justify duplicate math engines.
- A named ability may contain several consequences. Decompose it and classify each consequence independently.
- Never create a named resolver when an existing universal capability can express the mathematical outcome.

The combat log must retain the accurate source name. Engine identity and source identity are separate concepts.

Before adding code for any named feature, ask:

> If another monster, pregen, or homebrew feature had a different name but produced this exact same mathematical outcome, would it use this exact same primitive?

If not, generalize before certification.

## Combat-math scope

`docs/IRON_PIT_UNIVERSAL_COMBAT_DOCTRINE.md` and `docs/IRON_PIT_DAMAGE_SCOPE.md` are authoritative.

Model consequences that change supported Pit math, including:

- attack/save probability, Advantage/Disadvantage, AC, save DC, and roll modifiers;
- damage dice, flat damage, type, critical interaction, recurring damage, target count, and area damage;
- resistance, immunity, vulnerability, reduction, prevention;
- HP, max HP, healing, regeneration, Temporary HP;
- Action, Bonus Action, Reaction, Extra Attack, Multiattack, Legendary Action, and other supported action-economy opportunities;
- spell slots, recharge, limited uses, and resources that constrain legal combat output;
- conditions through their supported mathematical consequences;
- range, reach, adjacency, and target legality needed to determine whether a selected action can resolve.

Do not classify a whole feature by its name or by one harmless rider. Resolve mixed abilities component by component.

Examples:

- `Prone + Speed effect`: preserve Prone's attack-math consequences; ignore the movement-only part.
- `Push 10 feet + 2d6 damage`: resolve the damage; ignore the push unless another supported consequence depends on it.
- `Speed -10 + attack Disadvantage`: ignore Speed; apply universal Disadvantage.
- Ray of Frost: resolve spell attack and cold damage; ignore Speed reduction.
- Fireball: resolve target legality, Dexterity save, fire damage, and half damage on success; ignore object ignition.

Conditions are bundles of universal consequences, not separate private math systems. Prone, for example, contributes universal Advantage/Disadvantage effects while its current movement/standing-cost component is outside the simplified movement policy.

## Arena policy

`docs/ARENA_POLICY.md` is authoritative.

The standard Pit is fixed at **3 columns x 4 rows = 12 combat slots**:

- 6 monster slots;
- 6 pregen/hero slots.

It is a slug-fest board used to make engagement, range, reach, adjacency, targeting, area effects, and simple closing deterministic. It is not a full tactical movement simulator.

- Combatants are autonomous pawns compelled to fight until one side is dead.
- There is no voluntary retreat, fleeing, kiting, or keep-away AI.
- When comparing legal offensive options, prefer highest expected damage after hit/save probability, Advantage/Disadvantage, target count, resource legality, and known defenses.
- Do not hoard limited-use or recharge offense for a later encounter.
- If no damaging action is legal only because engagement has not occurred, close or Dash toward the fight.
- Base range, reach, adjacency, and target legality remain real.
- Movement-only Speed changes, forced movement, dragging, pushing, pulling, pathfinding, and similar tactical movement consequences do not block certification by themselves.
- If a mixed ability also changes supported combat math, model the supported component and ignore only movement.
- Existing D&D five-foot-square conventions remain the working distance convention unless explicitly changed later.

Aquatic-only creatures that cannot participate meaningfully in the standard land Pit are environment-deferred, not current universal-engine implementation debt. Mark them explicitly, e.g. `deferred-environment:aquatic-only`.

## Immutable card rule

Monster, pregen, and homebrew definitions are immutable source cards/templates.

Combat creates disposable runtime state. Current HP, Temporary HP, conditions, buffs/debuffs, effective modifiers, Concentration, resources, recharge state, and other temporary values may change during a fight but must never permanently rewrite the source definition. Every new fight starts from the original card.

## Canonical hero architecture

`docs/CANONICAL_COMBAT_BUILD_POLICY.md` is authoritative for canonical hero construction and mass production.

The product contains 12 persistent named canonical heroes, one per core class, across levels 1 through 20: exactly 240 hero level snapshots. The user selects `Hero -> Level -> Fight`; identity persists across progression.

- Each class has exactly one canonical progression identity unless the user explicitly authorizes a new architecture.
- Each level derives from the previous certified level by applying only that level's RAW combat delta. Do not hand-build 20 separate versions of one hero.
- Per-level research is delta triage, not a rebuild.
- Any new/scaled feature that changes supported Pit combat math must be modeled or remain an explicit blocker.
- Legal noncombat choices with no Pit consequence may be chosen deterministically without custom engine logic.
- The universal legal base array is the 27-point-buy `15 / 14 / 13 / 10 / 10 / 10` before legal Background increases and later feats/ASIs.
- Strength-primary melee defaults to STR 15 / CON 14 / DEX 13 with INT/WIS/CHA 10.
- Dexterity-primary melee/ranged defaults to DEX 15 / CON 14 / STR 13 with INT/WIS/CHA 10.
- Primary casters keep STR/DEX/CON at 10 and assign 15/14/13 to mental abilities using deterministic class priorities in `docs/CANONICAL_COMBAT_BUILD_POLICY.md`.
- Use only legal 2024 Background ability increases. Never invent species ability-score bonuses.
- Existing profiles that predate canonical build policy are migration debt and must be reconciled before extending that progression.
- Progression must update every applicable in-scope combat datum: level, proficiency, HP, ASIs/feats, subclass, AC, attacks, attack/damage bonuses, relevant saves, equipment, weapon masteries, resources, action economy, Extra Attack, spellcasting/slots, healing/defenses, class/subclass effects, and scaling.
- Only explicitly certified levels may be selectable or runnable.
- Karnok Stoneward is the Fighter progression. Rokhan Stonefury is the Barbarian progression. Remaining identities are defined by `backend/app/content/hero_progressions.py`.
- Caster classes reuse one deterministic canonical class spell package. A new level extends the same package rather than inventing a new spellbook.
- Every caster level must receive its full class-appropriate prepared/known damaging package target and spell-slot allotment before promotion.
- Spell upcasting remains deliberately deferred until explicitly reactivated and separately certified.
- Cantrip scaling by character level remains required.
- Melee loadouts follow one repeatable policy: DEX-primary favors dual wielding; STR-primary with shield training favors one-hander + shield; STR power builds favor a two-hander.
- Hero and monster behavior must reuse the same Universal Combat Capability whenever their in-scope RAW behavior is mathematically equivalent.
- One authoritative canonical definition should generate runtime/browser/catalog/certification state wherever practical. Repeated hand-authored ready lists and duplicated facts are migration debt.
- Certification is derived from audited build/profile data, runtime templates, Python gates, browser-generated parity, and public catalog readiness. Never certify by editing a manifest alone.

## Monster and homebrew architecture

The canonical SRD 5.2.1 catalog contains exactly 330 monsters. Treat certification as a source-driven capability pipeline, not 330 unrelated handcrafted projects:

`source -> parse/normalize -> decompose named abilities into consequences -> map consequences to universal capabilities -> runtime template -> Python certification -> browser parity -> generated assets -> public readiness -> exact-head CI`

This exact lifecycle also applies to future pregens and homebrew.

- A card using only already-supported in-scope primitives should require mostly data, not new resolver code.
- A card with a genuinely unsupported combat-math consequence remains blocked with explicit machine-readable blockers.
- Out-of-scope riders do not block otherwise accurate capability certification.
- After adding a shared primitive, re-audit all relevant monsters/pregens because many may unlock at once.
- Prefer capability tranches that maximize reuse rather than implementing one named monster at a time.
- Runtime data should contain source identity plus combat-relevant stats, attacks, defenses, resources, spells, conditions/effects, and universal capability IDs required to resolve the current Pit abstraction.

## Durable certification state

- `data/hero_certification_manifest.json` and `data/monster_certification_manifest.json` are generated snapshots, not hand-authored claims.
- Regenerate them with `python scripts/verify_certification_manifests.py --write` only after authoritative source/runtime/generated state is correct.
- Verify them with `python scripts/verify_certification_manifests.py` and report progress with `python scripts/report_certification_progress.py`.
- Do not maintain hundreds of duplicate Markdown checkboxes or hand-edited totals.
- CI must independently prove identity/slot counts, catalog counts, runtime readiness, source references, Python/browser parity, generated-static parity, blocker presence, and exact checked head.

## Validation and checkpoint policy

Before claiming a capability or certification tranche complete:

1. Run `python scripts/check_source_limits.py`.
2. Run `python scripts/prepare_static_site.py` and prove generated-static parity is clean.
3. Run `python scripts/verify_certification_manifests.py`.
4. Run the full Python suite from `backend` with `pytest -q`.
5. Run JavaScript syntax checks and every permanent browser `*.test.cjs` regression.
6. Confirm the exact intended commit is the commit certified by GitHub Actions.
7. Record exact certification counts and remaining blocker families using the generated report.

Work in coherent, reviewable commits. Code existence is not completion; every defined permanent gate must pass on the exact intended commit.

## Netlify resource policy

Do not hammer Netlify.

- Do not trigger Netlify deployments for routine commits or iterative testing.
- Prefer local Python/browser tests, generated-static validation, and GitHub CI.
- Batch work before any hosting verification.
- Use Netlify only at deliberate release/checkpoint validations where production hosting itself must be tested.
- Do not repeatedly poll or redeploy Netlify, and avoid unnecessary build-token or credit use.
- A green local/GitHub certification cycle does not automatically require Netlify. If a claim can be proven without Netlify, prove it without Netlify.

## Goal-mode policy

The full 240-hero/330-monster program is an open-ended master program, not one `/goal`. Use `docs/IRON_PIT_MASTER_PLAN.md` as durable program memory and choose finite goals with verifiable stopping conditions.

A normal sequence is:

1. Implement or refine one reusable universal combat capability.
2. Re-audit every pregen/monster/homebrew candidate affected by that capability.
3. Certify everything whose in-scope blockers reach zero.
4. Continue by highest shared-capability yield rather than by one-off named-card fixes.

Stop only for a genuine RAW/combat-scope ambiguity, security/permission issue, usage limit, or a decision that materially requires human input.
