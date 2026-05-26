from services.exercise_catalog_service import seed_exercise_catalog


def main() -> None:
    entries = seed_exercise_catalog()
    print(f"Seeded exercise catalog entries: {len(entries)}")
    for entry in entries:
        equipment = ", ".join(entry.equipment_required)
        muscles = ", ".join(entry.primary_muscle_groups)
        print(
            f"- {entry.name} | {entry.movement_pattern} | " f"{equipment} | {muscles}"
        )


if __name__ == "__main__":
    main()
