"""edgartools stays behind `SECDataClientAdapter`.

A future swap to sec-api or Calcbench must touch one file. This test fails the
moment a second module in `ledgerqa/` reaches for edgartools directly.
"""

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "ledgerqa"
ADAPTER_MODULE = PACKAGE_ROOT / "sec_adapter.py"

EDGARTOOLS_TOP_LEVEL_MODULES = {"edgar", "edgartools"}


def _imported_modules(source: str) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    return modules


def test_only_the_adapter_imports_edgartools():
    offenders = sorted(
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob("*.py")
        if path != ADAPTER_MODULE
        and _imported_modules(path.read_text(encoding="utf-8")) & EDGARTOOLS_TOP_LEVEL_MODULES
    )

    assert offenders == []


def test_the_adapter_is_where_edgartools_actually_lives():
    """Guards the test above from silently passing if the adapter is renamed
    away and nothing imports edgartools at all."""
    adapter_imports = _imported_modules(ADAPTER_MODULE.read_text(encoding="utf-8"))

    assert adapter_imports & EDGARTOOLS_TOP_LEVEL_MODULES
