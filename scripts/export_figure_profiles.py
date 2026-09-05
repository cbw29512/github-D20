from __future__ import annotations

import json
import logging
from pathlib import Path

from app.content.figure_profile_registry import reviewed_monster_figure_profiles

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "frontend" / "figure-profiles.js"


def render() -> str:
    payload = json.dumps(reviewed_monster_figure_profiles(), separators=(",", ":"), sort_keys=True)
    return (
        "/* GENERATED from the reviewed RAW-ready monster figure registry. Do not hand-edit. */\n"
        "(() => {\n  \"use strict\";\n"
        f"  window.IRON_PIT_MONSTER_FIGURE_PROFILES = {payload};\n"
        "})();\n"
    )


def main() -> None:
    try:
        profiles = reviewed_monster_figure_profiles()
        DESTINATION.write_text(render(), encoding="utf-8")
        logger.info("Exported %s reviewed monster figure profiles.", len(profiles))
    except Exception:
        logger.exception("Monster figure profile export failed.")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
