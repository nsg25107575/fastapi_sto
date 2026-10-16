import importlib
import pkgutil
from collections.abc import Iterable
from pathlib import Path

from seeders.base import Seeder


def discover_seeders() -> dict[str, type[Seeder]]:
    seeders: dict[str, type[Seeder]] = {}
    content_path = Path(__file__).parent / "content"
    for module_info in pkgutil.iter_modules([str(content_path)]):
        if not module_info.name.endswith("_seeder"):
            continue
        module = importlib.import_module(f"{__package__}.content.{module_info.name}")
        for candidate in vars(module).values():
            if (
                    isinstance(candidate, type)
                    and issubclass(candidate, Seeder)
                    and candidate is not Seeder
                    and candidate.__module__ == module.__name__
            ):
                name = module_info.name.removesuffix("_seeder")
                seeders[name] = candidate
    return dict(sorted(seeders.items()))


def resolve_seeder_order(
        seeders: dict[str, type[Seeder]],
        targets: Iterable[type[Seeder]] | None = None,
) -> list[type[Seeder]]:
    registered = set(seeders.values())
    ordered: list[type[Seeder]] = []
    completed: set[type[Seeder]] = set()
    visiting: list[type[Seeder]] = []

    def visit(seeder_class: type[Seeder]) -> None:
        if seeder_class not in registered:
            raise ValueError(
                f"Seeder dependency {seeder_class.__name__} is not registered."
            )
        if seeder_class in completed:
            return
        if seeder_class in visiting:
            cycle = " -> ".join(
                item.__name__ for item in (*visiting, seeder_class)
            )
            raise ValueError(f"Circular seeder dependency: {cycle}")

        visiting.append(seeder_class)
        for dependency in seeder_class.depends_on:
            if not isinstance(dependency, type) or not issubclass(
                    dependency, Seeder
            ):
                raise TypeError(
                    f"{seeder_class.__name__}.depends_on must contain "
                    "Seeder classes."
                )
            visit(dependency)
        visiting.pop()
        completed.add(seeder_class)
        ordered.append(seeder_class)

    for target in targets if targets is not None else seeders.values():
        visit(target)
    return ordered
