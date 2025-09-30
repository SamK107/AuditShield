import importlib
import pkgutil


def _safe_import(pkg_name: str):
    try:
        pkg = importlib.import_module(pkg_name)
    except ModuleNotFoundError:
        return None
    return pkg


def test_management_commands_import():
    # Add your apps that host custom commands
    candidates = [
        "store.management.commands",
        "downloads.management.commands",
    ]
    for pkg_name in candidates:
        pkg = _safe_import(pkg_name)
        if not pkg:
            continue
        for mod in pkgutil.iter_modules(pkg.__path__):
            importlib.import_module(f"{pkg_name}.{mod.name}")
