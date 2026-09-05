from __future__ import annotations

import re
from collections import defaultdict

from app.content.arena_eligibility import deferred_environment_reason
from app.content.blocker_yield import build_blocker_signatures, single_family_yields
from app.content.monster_catalog import build_monster_catalog, load_monster_rows
from app.content.monster_trait_source_audit import _ARENA_NEUTRAL_TRAITS, _MODELED_TRAITS, combat_relevant_trait_names
from app.domain.catalog import CoverageStatus
from report_zero_engine_monsters import _NONCOMBAT, _source_blockers

_SIGNATURE_LIMIT = 25
_ALLOWED_TRAITS = set(_ARENA_NEUTRAL_TRAITS) | set(_MODELED_TRAITS)
_CONTROL_EFFECT = re.compile(
    r"\b(blinded|charmed|frightened|incapacitated|paralyzed|petrified|poisoned|prone|restrained|stunned|unconscious|swallow(?:s|ed)?)\b",
    re.I,
)


def _unsupported_traits(row: dict[str, object]) -> tuple[str, ...]:
    relevant = combat_relevant_trait_names(row.get("traits", ""))
    return tuple(sorted(trait for trait in relevant if trait not in _ALLOWED_TRAITS))


def _trait_heading_yields(rows_by_name: dict[str, dict[str, object]], names: list[str]) -> dict[str, list[str]]:
    yields: dict[str, list[str]] = defaultdict(list)
    for name in names:
        unsupported = _unsupported_traits(rows_by_name[name])
        if not unsupported:
            raise RuntimeError(f"Trait-only blocker {name!r} has no outcome-changing unsupported trait heading.")
        for trait in unsupported:
            yields[trait].append(name)
    return {trait: sorted(monsters) for trait, monsters in sorted(yields.items(), key=lambda item: (-len(item[1]), item[0]))}


def _single_trait_heading_yields(
    rows_by_name: dict[str, dict[str, object]], names: list[str]
) -> dict[str, list[str]]:
    yields: dict[str, list[str]] = defaultdict(list)
    for name in names:
        unsupported = _unsupported_traits(rows_by_name[name])
        if len(unsupported) == 1:
            yields[unsupported[0]].append(name)
    return {trait: sorted(monsters) for trait, monsters in sorted(yields.items(), key=lambda item: (-len(item[1]), item[0]))}


def _normalize_control_effect(value: str) -> str:
    normalized = value.lower()
    if normalized.startswith("swallow"):
        return "swallow"
    return normalized


def _control_effects(row: dict[str, object]) -> tuple[str, ...]:
    actions = str(row.get("actions", ""))
    effects = {_normalize_control_effect(match.group(1)) for match in _CONTROL_EFFECT.finditer(actions)}
    if not effects:
        raise RuntimeError(f"Control blocker {row.get('name')!r} has no recognized outcome-changing control effect.")
    return tuple(sorted(effects))


def _control_effect_yields(
    rows_by_name: dict[str, dict[str, object]], names: list[str]
) -> dict[str, list[str]]:
    yields: dict[str, list[str]] = defaultdict(list)
    for name in names:
        for effect in _control_effects(rows_by_name[name]):
            yields[effect].append(name)
    return {effect: sorted(monsters) for effect, monsters in sorted(yields.items(), key=lambda item: (-len(item[1]), item[0]))}


def _control_signatures(
    rows_by_name: dict[str, dict[str, object]], names: list[str]
) -> dict[tuple[str, ...], list[str]]:
    grouped: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for name in names:
        grouped[_control_effects(rows_by_name[name])].append(name)
    return {signature: sorted(monsters) for signature, monsters in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))}


def main() -> None:
    rows = load_monster_rows()
    rows_by_name = {str(row["name"]): row for row in rows}
    monster_names = set(rows_by_name)
    cards = build_monster_catalog()
    ready_names = {card.name for card in cards if card.coverage_status is CoverageStatus.RAW_READY}
    catalog_blocked = sum(card.coverage_status is not CoverageStatus.RAW_READY for card in cards)
    blockers_by_name: dict[str, list[str]] = {}
    environment_deferred: list[str] = []
    noncombat_deferred: list[str] = []
    for row in rows:
        name = str(row["name"])
        if name in ready_names:
            continue
        if deferred_environment_reason(row["speed"]) is not None:
            environment_deferred.append(name)
            continue
        blockers = _source_blockers(row, monster_names)
        if blockers == [_NONCOMBAT]:
            noncombat_deferred.append(name)
            continue
        blockers_by_name[name] = blockers or ["unclassified-source-audit-gap"]

    signatures = build_blocker_signatures(blockers_by_name)
    singles = single_family_yields(signatures)
    trait_only = singles.get("trait", [])
    control_only = singles.get("condition-or-control", [])
    print(
        "CAPABILITY_YIELD_BASELINE"
        f"\tready={len(ready_names)}\tblocked={catalog_blocked}"
        f"\tactionable_blocked={len(blockers_by_name)}"
        f"\tdeferred={len(environment_deferred) + len(noncombat_deferred)}"
        f"\tsignatures={len(signatures)}"
    )
    if environment_deferred:
        print("CAPABILITY_DEFERRED_ENVIRONMENT\t" + " | ".join(sorted(environment_deferred)))
    if noncombat_deferred:
        print("CAPABILITY_DEFERRED_NONCOMBAT\t" + " | ".join(sorted(noncombat_deferred)))
    for blocker, names in sorted(singles.items(), key=lambda item: (-len(item[1]), item[0])):
        print(f"CAPABILITY_SINGLE_FAMILY\t{blocker}\t{len(names)}\t" + " | ".join(names))
    for signature, names in _control_signatures(rows_by_name, control_only).items():
        print(f"CAPABILITY_CONTROL_SIGNATURE\t{'+'.join(signature)}\t{len(names)}\t" + " | ".join(names))
    for effect, names in _control_effect_yields(rows_by_name, control_only).items():
        print(f"CAPABILITY_CONTROL_EFFECT\t{effect}\t{len(names)}\t" + " | ".join(names))
    for trait, names in _single_trait_heading_yields(rows_by_name, trait_only).items():
        print(f"CAPABILITY_TRAIT_SINGLE_HEADING\t{trait}\t{len(names)}\t" + " | ".join(names))
    for trait, names in _trait_heading_yields(rows_by_name, trait_only).items():
        print(f"CAPABILITY_TRAIT_HEADING\t{trait}\t{len(names)}\t" + " | ".join(names))
    for index, (signature, names) in enumerate(signatures.items()):
        if index >= _SIGNATURE_LIMIT:
            break
        label = "+".join(signature) if signature else "none"
        print(f"CAPABILITY_SIGNATURE\t{len(names)}\t{label}\t" + " | ".join(names))


if __name__ == "__main__":
    main()
