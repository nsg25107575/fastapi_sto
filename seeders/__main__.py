import argparse

from database.engine import SessionLocal
from seeders.registry import discover_seeders, resolve_seeder_order


def main() -> None:
    seeders = discover_seeders()
    parser = argparse.ArgumentParser(description="Run database seeders.")
    parser.add_argument(
        "--seeder",
        choices=("all", *seeders),
        default="all",
        help="Seeder to run (default: all).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available seeders without running them.",
    )
    args = parser.parse_args()

    if args.list:
        print("\n".join(seeders))
        return

    targets = (
        seeders.values()
        if args.seeder == "all"
        else (seeders[args.seeder],)
    )
    with SessionLocal() as session, session.begin():
        for seeder_class in resolve_seeder_order(seeders, targets):
            seeder_class().run(session)

    print(f"Database seeding complete: {args.seeder}")


if __name__ == "__main__":
    main()
