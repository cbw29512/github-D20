from app.content.mechanic_family_inventory import (
    build_hero_mechanic_demand,
    build_monster_mechanic_families,
)


def main() -> None:
    families = build_monster_mechanic_families()
    hero_demand = build_hero_mechanic_demand()
    for family in families:
        print(
            f"MECHANIC_FAMILY\t{family.id}\t{family.demand_count}\t"
            + " | ".join(family.monster_names)
        )
    for mechanic_id, owners in sorted(
        hero_demand.items(), key=lambda item: (-len(item[1]), item[0])
    ):
        print(
            f"HERO_MECHANIC_DEMAND\t{mechanic_id}\t{len(owners)}\t"
            + " | ".join(owners)
        )


if __name__ == "__main__":
    main()
