from __future__ import annotations

import re
from typing import Any


def _area_pattern(shape: str, size_ft: int, width_ft: int | None) -> re.Pattern[str]:
    foot = rf"{size_ft}\s*[-–]?\s*foot(?:-long)?"
    if shape in {"cone", "cube"}:
        return re.compile(rf"\b{foot}\s+{shape}\b", re.IGNORECASE)
    if shape == "line":
        width = rf"{width_ft}\s*[-–]?\s*foot(?:-wide)?" if width_ft else r"\d+\s*[-–]?\s*foot(?:-wide)?"
        return re.compile(
            rf"(?=[^.]*\b{foot}\b)(?=[^.]*\b{width}\b)(?=[^.]*\bline\b)[^.]+",
            re.IGNORECASE,
        )
    return re.compile(rf"\b{foot}[^.]*\bradius\b|\b{size_ft}\s*[-–]?\s*foot-radius\b", re.IGNORECASE)


def save_math_issues(action: Any, actions: str) -> list[str]:
    """Verify source math that generic save-action parsing did not previously cover."""
    issues: list[str] = []
    if action.damage_type and not re.search(rf"\b{re.escape(str(action.damage_type))}\s+damage\b", actions, re.IGNORECASE):
        issues.append(f"save-damage-type-missing:{action.id}")
    if action.success_damage == "half" and not re.search(r"\bSuccess:\s*Half\s+damage\b", actions, re.IGNORECASE):
        issues.append(f"save-success-half-mismatch:{action.id}")
    if action.area is not None:
        if not _area_pattern(action.area.shape, action.area.size_ft, action.area.width_ft).search(actions):
            issues.append(f"save-area-mismatch:{action.id}")
    return issues
