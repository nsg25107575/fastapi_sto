import importlib
import pkgutil
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
