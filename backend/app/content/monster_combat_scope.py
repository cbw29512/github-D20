from __future__ import annotations

import re

_SPACE = re.compile(r"\s+")
_ANNOTATION = re.compile(r"\s*\([^)]*\)\s*$")

# Iron Pit scope is intentionally narrower than the full tabletop ruleset.
# Movement, positioning, senses, stealth, environment, and narrative-only text
# do not block certification unless the same feature also changes combat math
# or meaningful action economy.
_COMBAT_MATH = (
    re.compile(r"\bdamage\b", re.I),
    re.compile(r"\bHit Points?\b|\bTemporary Hit Points?\b", re.I),
    re.compile(r"\bAC\b|\bArmor Class\b", re.I),
    re.compile(r"\battack roll(?:s)?\b|\bdamage roll(?:s)?\b|\bto hit\b", re.I),
    re.compile(r"\bsaving throw(?:s)?\b|\bsave DC\b|\bD20 Test(?:s)?\b", re.I),
    re.compile(r"\binitiative\b|\bcritical hit(?:s)?\b|\bConcentration\b", re.I),
    re.compile(
        r"\b(?:blinded|charmed|frightened|incapacitated|paralyzed|petrified|poisoned|prone|restrained|stunned|unconscious)\b",
        re.I,
    ),
    re.compile(r"\b(?:heavily obscured|invisible|invisibility)\b", re.I),
    re.compile(
        r"\b(?:can't|cannot)\s+(?:take|use)\s+(?:an?\s+)?(?:Action|Bonus Action|Reaction)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:takes?|gains?|uses?)\s+(?:an?\s+)?(?:additional|extra)\s+(?:Action|Bonus Action|Reaction)\b",
        re.I,
    ),
    re.compile(r"\bmakes?\s+(?:one|two|three|four|an?)\b[^.]{0,70}\battack\b", re.I),
    re.compile(r"\bcasts?\b", re.I),
    re.compile(
        r"\b(?:add(?:s)?|subtract(?:s)?)\s+[+-]?\d+\s+(?:to|from)\s+(?:the|that|its|their)?\s*roll\b",
        re.I,
    ),
    re.compile(
        r"\b(?:Advantage|Disadvantage)\b[^.]{0,90}\b(?:attack|saving throw|D20 Test)\b"
        r"|\b(?:attack|saving throw|D20 Test)\b[^.]{0,90}\b(?:Advantage|Disadvantage)\b",
        re.I,
    ),
)


def normalized_source_text(value: object) -> str:
    return _SPACE.sub(" ", str(value or "")).strip()


def base_feature_name(name: str) -> str:
    return _ANNOTATION.sub("", normalized_source_text(name)).strip()


def feature_blocks(source: object, headings: list[str] | tuple[str, ...]) -> dict[str, str]:
    """Split a reviewed SRD section by already-parsed headings without guessing new headings."""
    text = normalized_source_text(source)
    if not text:
        return {}
    located: list[tuple[int, int, str]] = []
    for heading in headings:
        marker = f"{normalized_source_text(heading)}."
        start = text.find(marker)
        if start < 0:
            raise ValueError(f"SRD feature heading {heading!r} was not found in source section.")
        located.append((start, start + len(marker), heading))
    located.sort(key=lambda item: item[0])
    blocks: dict[str, str] = {}
    for index, (start, _, heading) in enumerate(located):
        end = located[index + 1][0] if index + 1 < len(located) else len(text)
        blocks[heading] = text[start:end].strip()
    return blocks


def combat_math_relevant(source: object) -> bool:
    """Return True only when source text can change an Iron Pit combat outcome."""
    text = normalized_source_text(source)
    if not text:
        return False
    # A returned/thrown weapon, forced movement, Speed change, teleport, Hide,
    # Disengage, sensory output, and similar movement/presentation mechanics are
    # deliberately absent here. If they also alter math, another signal below
    # still catches the feature.
    return any(pattern.search(text) for pattern in _COMBAT_MATH)


def arena_neutral_features(source: object, headings: list[str] | tuple[str, ...]) -> set[str]:
    blocks = feature_blocks(source, headings)
    return {heading for heading, block in blocks.items() if not combat_math_relevant(block)}
