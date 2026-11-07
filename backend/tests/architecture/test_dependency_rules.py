"""Kiểm tra quy tắc kiến trúc bằng cách đọc import trong code (không cần chạy app).
Vi phạm -> test đỏ -> CI đỏ. Xem backend/README.md phần "Quy tắc"."""
import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"
MODULES_DIR = APP / "modules"
MODULES = sorted(p.name for p in MODULES_DIR.iterdir() if p.is_dir() and not p.name.startswith("__"))

# Module -> các module nó được phụ thuộc. Thêm module mới thì cập nhật bảng này.
ALLOWED_DEPENDENCIES: dict[str, set[str]] = {
    "auth": set(),
    "cards": set(),
    "spreads": set(),
    "quota": set(),
    "readings": {"quota", "cards", "spreads"},
}

FRAMEWORK_PREFIXES = (
    "fastapi", "starlette", "sqlalchemy", "pydantic", "alembic",
    "google", "jwt", "bcrypt", "psycopg",
)


def imports_of(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append(node.module)
    return found


def module_files():
    for module in MODULES:
        for path in (MODULES_DIR / module).rglob("*.py"):
            layer = path.relative_to(MODULES_DIR / module).parts[0]
            yield module, layer, path


def test_every_module_is_declared():
    assert set(MODULES) == set(ALLOWED_DEPENDENCIES), "Cập nhật ALLOWED_DEPENDENCIES"


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_inner_layers_do_not_import_frameworks(layer):
    errors = []
    for _module, lyr, path in module_files():
        if lyr != layer:
            continue
        for imp in imports_of(path):
            if imp.startswith(FRAMEWORK_PREFIXES):
                errors.append(f"{path.relative_to(APP)} import {imp}")
    assert not errors, "\n".join(errors)


def test_inner_layers_do_not_import_outer_layers_of_same_module():
    errors = []
    for module, layer, path in module_files():
        if layer not in ("domain", "application"):
            continue
        forbidden = ["infrastructure", "presentation"]
        if layer == "domain":
            forbidden.append("application")
        for imp in imports_of(path):
            for f in forbidden:
                if imp.startswith(f"app.modules.{module}.{f}"):
                    errors.append(f"{path.relative_to(APP)} import {imp}")
    assert not errors, "\n".join(errors)


def test_infrastructure_does_not_import_presentation():
    errors = []
    for _module, layer, path in module_files():
        if layer != "infrastructure":
            continue
        for imp in imports_of(path):
            if ".presentation" in imp:
                errors.append(f"{path.relative_to(APP)} import {imp}")
    assert not errors, "\n".join(errors)


def test_modules_only_depend_on_allowed_modules():
    errors = []
    for module, layer, path in module_files():
        for imp in imports_of(path):
            parts = imp.split(".")
            if parts[:2] != ["app", "modules"] or len(parts) < 3:
                continue
            other = parts[2]
            if other == module:
                continue
            if other not in ALLOWED_DEPENDENCIES[module]:
                # Ngoại lệ hẹp: tầng presentation của module khác được dùng
                #   - auth.presentation.dependencies (get_current_user, require_admin)
                #   - auth.domain (User, Role) để biết ai đang đăng nhập / có phải admin
                if other == "auth" and path.name in ("router.py", "dependencies.py") and layer == "presentation" and (
                    imp.endswith("presentation.dependencies") or imp.startswith("app.modules.auth.domain")
                ):
                    continue
                errors.append(f"{path.relative_to(APP)} import {imp}")
            elif path.name != "dependencies.py":
                # module khác chỉ được import domain / application, trừ file lắp ráp
                sub = parts[3] if len(parts) > 3 else ""
                if sub not in ("domain", "application"):
                    errors.append(f"{path.relative_to(APP)} import {imp}")
    assert not errors, "\n".join(errors)


def test_no_dependency_cycles():
    def visit(node, stack):
        assert node not in stack, f"Vòng phụ thuộc: {' -> '.join(stack + [node])}"
        for nxt in ALLOWED_DEPENDENCIES[node]:
            visit(nxt, stack + [node])

    for m in MODULES:
        visit(m, [])


def test_shared_does_not_import_modules():
    errors = []
    for path in (APP / "shared").rglob("*.py"):
        for imp in imports_of(path):
            if imp.startswith("app.modules"):
                errors.append(f"{path.relative_to(APP)} import {imp}")
    assert not errors, "\n".join(errors)
