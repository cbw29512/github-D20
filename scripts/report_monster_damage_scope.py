from __future__ import annotations

from collections import Counter

from app.content.monster_catalog import load_monster_rows
from app.content.monster_damage_scope_audit import audit_monster_damage_scope


def main() -> None:
    audits = [audit_monster_damage_scope(row) for row in load_monster_rows()]
    counts = Counter(family for audit in audits for family in audit.families)
    names: dict[str, list[str]] = {}
    for audit in audits:
        for family in audit.families:
            names.setdefault(family, []).append(audit.monster_name)

    print(f"MONSTER_DAMAGE_SCOPE\tcatalog\t{len(audits)}")
    for family, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"MONSTER_DAMAGE_FAMILY\t{family}\t{count}")
        if count <= 30:
            print(f"MONSTER_DAMAGE_NAMES\t{family}\t" + " | ".join(sorted(names[family])))


if __name__ == "__main__":
    main()
