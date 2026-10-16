import re
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m seeders.create <SeederName>")

    name = sys.argv[1]
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", name):
        raise SystemExit("Seeder name must be PascalCase, e.g. ExampleSeeder.")

    class_name = name if name.endswith("Seeder") else f"{name}Seeder"
    base_name = class_name.removesuffix("Seeder")
    slug = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name).lower()
    content_directory = Path(__file__).parent / "content"
    content_directory.mkdir(exist_ok=True)
    destination = content_directory / f"{slug}_seeder.py"

    if destination.exists():
        raise SystemExit(f"Seeder already exists: {destination.name}")

    destination.write_text(
        "from sqlalchemy.orm import Session\n\n"
        "from seeders.base import Seeder\n\n\n"
        f"class {class_name}(Seeder):\n"
        "    depends_on = ()\n\n"
        "    def run(self, session: Session) -> None:\n"
        "        \"\"\"Add this seeder's database changes here.\"\"\"\n"
        "        pass\n",
        encoding="utf-8",
    )
    print(f"Created {destination}")


if __name__ == "__main__":
    main()
